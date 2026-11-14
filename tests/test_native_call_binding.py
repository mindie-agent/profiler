"""BIND1 native-call indexing, signature matching, HCCL alias rules, and replay cache identity.

[Role]
  Verify ``StructureTargets`` and ``StructureMapper`` consume ``mindie-sim``
  ``v0.9.11`` ``mindie-sim/native-call-binding/1`` records, check tensor
  signature compatibility before claiming correspondence, fallback from generic
  ``event.op_type`` wrappers to specific ``event.name`` kernels, enforce
  rank-local HCCL raw-identity boundaries, and reject missing/foreign
  ``prediction_identity`` entries in ``scoped_native_replay.read_prediction_cache``.

[Invariants]
  * Name + signature correspondence keeps ``tensor_match_implied == False`` and
    ``occurrence_binding_implied == False``.
  * Signed HCCL raw-task aliases match only exact ``(rank_id, global_task_id,
    stream_id, task_id, connection_id, device_id, start_ns, end_ns)`` tuples
    for the declared replica; cross-rank and cross-range reuse is rejected.
  * Legacy prediction cache entries without a matching ``prediction_identity``
    are treated as stale cache misses.

[Timeouts & Locks]
  Pure in-memory ``mindie_sim`` graph exports and ``tmp_path`` JSON files; no
  devices, sleeps, or locks.

[Side-Effect Policy]
  Writes only inside pytest ``tmp_path``.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from mindie_profiler.accounting import account_window
from mindie_profiler.events import Event, Observation, QueryStats, SourceRef, Window
from mindie_profiler.structure_mapping import StructureMapper
from mindie_profiler.structure_subgraphs import StructureTargets

ROOT = Path(__file__).resolve().parents[1]


def _qbmm_node(call_id: str = "c" * 64) -> dict:
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
            "api": {
                "namespace": "cann_kernel",
                "entry": "QuantBatchMatmulV3",
                "aclnn_symbol": None,
                "candidates": [],
            },
            "source": {
                "path": "quant_batch_matmul_v3/arch35/quant_batch_matmul_v3.cpp",
                "sha256": "13daf996890d70e7b1dc9275ab3a464043860e67d6df730e28742393c023ec88",
            },
            "typed": {
                "dtype": "int8",
                "layout": "int8_per_channel",
                "shapes": {"local": [64, 2048, 6144]},
            },
            "kernels": [
                {"name": "QuantBatchMatmulV3", "role": "cube", "evidence": "source_declared"}
            ],
            "evidence": {
                "entry": "source_declared",
                "aclnn_symbol": "unresolved",
                "source": "source_declared",
                "kernels": "source_declared",
                "core": "not_declared",
            },
            "unresolved": ["aclnn_symbol_unresolved", "execution_core_not_declared"],
        },
    }


def test_sim_call_identity_is_indexed_and_described_without_new_claims() -> None:
    node = _qbmm_node()
    record = {**node.pop("_native_call"), "node_id": node["node_id"]}
    # Pass duplicate record twice to ensure StructureTargets deduplicates cleanly.
    index = StructureTargets({node["node_id"]: node}, (), [record, record])
    assert index.native_calls[record["call_id"]] == [node["node_id"]]
    assert index.native_call_entries["QuantBatchMatmulV3"] == [node["node_id"]]
    assert index.native_call_kernels["QuantBatchMatmulV3"] == [node["node_id"]]
    described = index.describe_implementation("QuantBatchMatmulV3", (node["node_id"],))
    assert described["native_call"]["call_id"] == record["call_id"]
    assert described["native_call"]["entry"] == "QuantBatchMatmulV3"
    assert described["native_call"]["kernels"] == ["QuantBatchMatmulV3"]
    assert described["tensor_match_implied"] is False
    assert described["occurrence_binding_implied"] is False


def test_nodes_without_bind1_keep_the_previous_behaviour() -> None:
    node = _qbmm_node()
    node.pop("_native_call")
    index = StructureTargets({node["node_id"]: node}, ())
    assert dict(index.native_calls) == {}
    described = index.describe_implementation("QuantBatchMatmulV3", (node["node_id"],))
    assert described["native_call"] is None


def _mla_structure() -> dict:
    structure = pytest.importorskip("mindie_sim.structure")
    operators = pytest.importorskip("mindie_sim.prediction.operators.mla_decode")
    native_binding = pytest.importorskip("mindie_sim.prediction.native_binding")
    program = pytest.importorskip("mindie_sim.prediction.program")
    op = operators.make_op(
        {
            "implementation": operators.IMPLEMENTATION,
            "contexts": [16],
            "heads": 4,
            "key_heads": 1,
            "latent_dim": 256,
            "rope_dim": 32,
            "page_size": 16,
            "num_kv_splits": 2,
            "dtype": "bf16",
            "cache_dtype": "bf16",
            "is_mla": True,
            "is_hip": False,
        }
    )
    mapping = {"lowerings": {"mla_decode": "vllm_triton_mla_decode_tuple"}}
    expanded = list(program.RecipeBook.from_mapping(mapping).expand((op,)))
    stage_ids = [item.op_id for item in expanded if item.family != "barrier"]
    kernels = [
        {"name": "_fwd_grouped_kernel_stage1", "role": "mix", "evidence": "source_declared"},
        {"name": "_fwd_kernel_stage2", "role": "mix", "evidence": "source_declared"},
    ]
    expanded = [
        native_binding.declare_native_call(
            item,
            api={"namespace": "triton", "entry": "decode_attention_fwd_grouped"},
            source={"path": "vllm_ascend/ops/mla.py", "sha256": "b" * 64},
            kernels=kernels,
            members={"op_ids": stage_ids},
        )
        if item.family != "barrier"
        else item
        for item in expanded
    ]
    return structure.export_op_structure(
        {0: tuple(expanded), 1: tuple(expanded)},
        model={},
        execution={"phase": "decode"},
        kernels=mapping,
        native_evidence=True,
    )


def _control_event(
    name: str,
    *,
    op_type: str | None = None,
    shapes: str = "1,4,288",
    dtypes: str = "DT_BF16",
    out_shapes: str | None = None,
    out_dtypes: str | None = None,
    in_formats: str = "ND",
    out_formats: str = "ND",
    rank: str = "rank_0",
    rank_index: int = 0,
    task: str = "1",
) -> Event:
    return Event(
        rank_id=rank,
        rank_index=rank_index,
        name=name,
        op_type=op_type or name,
        task_type="MIX_AIC",
        core="MIX_AIC",
        stream_id="1",
        task_id=task,
        device_id="0",
        start_ns=0,
        end_ns=100,
        source_kind="db",
        table="COMPUTE_TASK_INFO",
        input_shapes=shapes,
        input_dtypes=dtypes,
        input_formats=in_formats,
        output_shapes=shapes if out_shapes is None else out_shapes,
        output_dtypes=dtypes if out_dtypes is None else out_dtypes,
        output_formats=out_formats,
        locator={"source": "/prepare-only", "task_rowid": 1},
    )


def _control_observation(
    events: list[Event], *, rank: str = "rank_0", rank_index: int = 0
) -> Observation:
    window = Window(0, 100, step=3)
    source = SourceRef(
        rank_id=rank,
        rank_index=rank_index,
        kind="db",
        path="/prepare-only",
        basename="prepare-only",
        sha256=None,
        size_bytes=1,
        schema_version="declared",
        schema_variant="prepare_only",
        mtime_ns=1,
    )
    return Observation(
        rank, rank_index, window, account_window(events, window), events, source, QueryStats(rank, "3")
    )


def _ordinary_correspondences(
    structure: dict,
    events: list[Event],
    *,
    rank: str = "rank_0",
    rank_index: int = 0,
    rank_replicas: dict[str, str] | None = None,
) -> list[dict | None]:
    bindings = None
    if rank_replicas:
        bindings = {
            "schema_version": "mindie-profile-bindings/1",
            "graph_id": structure["graph_id"],
            "rank_replicas": rank_replicas,
        }
    mapper = StructureMapper(structure, bindings=bindings)
    mapper.map_window(_control_observation(events, rank=rank, rank_index=rank_index))
    return [row.get("implementation_correspondence") for row in mapper.sample]


def test_ordinary_mapper_resolves_wrapper_and_generic_op_type_by_signature() -> None:
    structure = _mla_structure()
    names = ("decode_attention_fwd_grouped", "_fwd_grouped_kernel_stage1", "_fwd_kernel_stage2")
    events = [
        _control_event(names[0], task="0"),
        # Generic wrapper op_type="TritonKernel" falls back to specific event.name.
        _control_event(names[1], op_type="TritonKernel", task="1"),
        _control_event(names[2], task="2"),
    ]
    correspondences = _ordinary_correspondences(
        structure, events, rank_replicas={"rank_0": "0"}
    )
    assert len(correspondences) == 3
    call_ids = set()
    for name, correspondence in zip(names, correspondences):
        assert correspondence is not None, name
        assert correspondence["basis"] == "declared_native_call_signature"
        assert correspondence["rank"] == "rank_0"
        assert correspondence["signature_match"] is True
        call = correspondence["native_call"]
        assert call["entry"] == "decode_attention_fwd_grouped"
        assert call["kernels"] == ["_fwd_grouped_kernel_stage1", "_fwd_kernel_stage2"]
        assert call["declared_target_count"] == 2
        assert correspondence["occurrence_binding_implied"] is False
        assert correspondence["tensor_match_implied"] is False
        assert correspondence["observed_proof"] is False
        assert correspondence["prepare_only_control"] is True
        call_ids.add(call["call_id"])
    assert len(call_ids) == 1

    native_binding = pytest.importorskip("mindie_sim.prediction.native_binding")
    bindings_objs = [
        native_binding.NativeCallBinding(
            call_id=row["call_id"],
            op_id=row["op_id"],
            family=row["family"],
            recipe=row["recipe"],
            source_boundary=row["source_boundary"],
            api=row["api"],
            source=row["source"],
            typed=row["typed"],
            kernels=tuple(row["kernels"]),
        )
        for row in structure["native_calls"]
        if row["node_id"].startswith("rank:0/")
    ]
    joined = native_binding.join_profiler_rows(
        [{"name": item.name, "op_type": item.op_type} for item in events],
        bindings_objs,
    )
    assert joined["joined"] == 3
    assert joined["unmatched"] == 0


def test_ordinary_mapper_ranks_one_call_and_rejects_signature_mismatch() -> None:
    structure = _mla_structure()
    rank1 = _ordinary_correspondences(
        structure,
        [_control_event("_fwd_kernel_stage2", rank="rank_1", rank_index=1)],
        rank="rank_1",
        rank_index=1,
        rank_replicas={"rank_1": "1"},
    )[0]
    assert rank1 is not None
    assert rank1["rank"] == "rank_1"
    assert rank1["declared_node_ids"] == [
        "rank:1/mla_decode/stage1_grouped_decode",
        "rank:1/mla_decode/stage2_split_merge",
    ]
    assert rank1["signature_match"] is True
    for bad in (
        _control_event("decode_attention_fwd_grouped", dtypes="DT_FLOAT", task="8"),
        _control_event("decode_attention_fwd_grouped", shapes="1,4,289", task="9"),
        _control_event("decode_attention_fwd_grouped", shapes="777,1,4,288", task="10"),
        _control_event(
            "decode_attention_fwd_grouped", shapes="1,4,288;9,11", dtypes="DT_FLOAT;DT_BF16", task="11"
        ),
        _control_event(
            "decode_attention_fwd_grouped", shapes="1,4,288;9,11", dtypes="DT_BF16;DT_BF16", task="12"
        ),
        _control_event(
            "decode_attention_fwd_grouped", out_shapes="1,4,999", task="13"
        ),
        _control_event(
            "decode_attention_fwd_grouped", out_dtypes="DT_FLOAT", task="14"
        ),
        _control_event(
            "decode_attention_fwd_grouped", in_formats="FRACTAL_NZ", task="15"
        ),
    ):
        assert _ordinary_correspondences(structure, [bad])[0] is None


def test_hccl_alias_mapper_rejects_cross_rank_and_cross_range_reuse() -> None:
    schema = pytest.importorskip("mindie_sim.schema.operators")
    hccl_graph = pytest.importorskip("mindie_sim.prediction.hccl_graph")
    native_binding = pytest.importorskip("mindie_sim.prediction.native_binding")
    structure_module = pytest.importorskip("mindie_sim.structure")

    aliases = [
        {
            "rank_id": "rank_0",
            "logical_rank": 0,
            "global_task_id": "5",
            "stream_id": "26",
            "task_id": "17",
            "connection_id": "2",
            "device_id": "0",
            "start_ns": "1000",
            "end_ns": "2000",
            "compute_name": "AivKernel",
            "comm_name": "hcom_allGather__612_0_1",
        }
    ]
    op = schema.OpSpec(
        "s0.l0.tp_all_gather",
        "allgather",
        "decode",
        0,
        0,
        (),
        (5120,),
        (5120,),
        (5120,),
        (5120,),
        link_bytes=10240,
        dtype="bf16",
        metadata=(("group_axis", "tp"), ("collective", "allgather")),
    )
    lowered = list(hccl_graph.lower((op,), SimpleNamespace(kernels={}), "bf16"))
    lowered[0] = native_binding.declare_native_call(
        lowered[0],
        api={"namespace": "hccl", "entry": "HcclAllGather"},
        source={"path": "hccl/all_gather.cc", "sha256": "a" * 64},
        kernels=[{"name": "AivKernel", "role": "aiv", "evidence": "source_declared"}],
        observed_aliases=aliases,
    )
    structure = structure_module.export_op_structure(
        {0: tuple(lowered), 1: tuple(lowered)},
        model={},
        execution={"phase": "decode"},
        native_evidence=True,
    )
    bindings = {
        "schema_version": "mindie-profile-bindings/1",
        "graph_id": structure["graph_id"],
        "rank_replicas": {"rank_0": "0", "rank_1": "1"},
    }

    for rank, rank_index, device, start_ns, end_ns in (
        ("rank_1", 1, 0, 1000, 2000),
        ("rank_0", 0, 0, 1001, 2001),
        ("rank_2", 2, 2, 1000, 2000),
    ):
        event = Event(
            rank_id=rank,
            rank_index=rank_index,
            name="AivKernel",
            op_type="AivKernel",
            task_type="MIX_AIC",
            core="MIX_AIC",
            stream_id="26",
            task_id="17",
            device_id=str(device),
            start_ns=start_ns,
            end_ns=end_ns,
            source_kind="db",
            table="COMPUTE_TASK_INFO",
            locator={"global_task_id": "5", "connection_id": "2", "source": "/prepare-only"},
        )
        mapper = StructureMapper(structure, bindings=bindings)
        window = Window(start_ns, end_ns, step=3)
        source = SourceRef(
            rank_id=rank,
            rank_index=rank_index,
            kind="db",
            path="/prepare-only",
            basename="prepare-only",
            sha256=None,
            size_bytes=1,
            schema_version="1",
            schema_variant="raw",
            mtime_ns=1,
        )
        mapper.map_window(
            Observation(rank, rank_index, window, account_window([event], window), [event], source, QueryStats(rank, "3"))
        )
        assert mapper.sample[0]["implementation_correspondence"] is None
        assert mapper.sample[0].get("native_call_occurrence") is None


def test_prediction_cache_never_accepts_missing_or_foreign_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "examples" / "structure"))
    from scoped_native_replay import read_prediction_cache

    key = "a" * 64
    path = tmp_path / f"pred_{key}.json"
    path.write_text(json.dumps({"status": "modeled", "body_forward_span_ms": 1.0}), encoding="utf-8")
    assert read_prediction_cache(key, tmp_path) is None
    path.write_text(
        json.dumps({"status": "modeled", "prediction_identity": "b" * 64, "body_forward_span_ms": 1.0}),
        encoding="utf-8",
    )
    assert read_prediction_cache(key, tmp_path) is None
    path.write_text(
        json.dumps({"status": "modeled", "prediction_identity": key, "body_forward_span_ms": 1.0}),
        encoding="utf-8",
    )
    cached = read_prediction_cache(key, tmp_path)
    assert cached is not None and cached["body_forward_span_ms"] == 1.0


def test_native_call_format_cache_is_order_independent() -> None:
    structure = _mla_structure()
    nd_event = _control_event("decode_attention_fwd_grouped", in_formats="ND", task="10")
    nz_event = _control_event("decode_attention_fwd_grouped", in_formats="FRACTAL_NZ", task="11")
    forward = _ordinary_correspondences(
        structure, [nd_event, nz_event], rank_replicas={"rank_0": "0"}
    )
    reverse = _ordinary_correspondences(
        structure, [nz_event, nd_event], rank_replicas={"rank_0": "0"}
    )
    assert [item is not None for item in forward] == [True, False]
    assert [item is not None for item in reverse] == [False, True]


def test_declared_input_output_role_multiplicity_and_ambiguous_hccl_alias_guards() -> None:
    from mindie_profiler.structure_native_calls import _seal_digest

    def _seal(doc: dict) -> dict:
        body = {
            k: v
            for k, v in doc.items()
            if k not in {"graph_id", "source", "native_calls", "native_call_coverage"}
        }
        return {**doc, "graph_id": _seal_digest(body)}

    # 1. Explicit inputs/outputs roles and multiplicity cannot be swapped or duplicated!
    pure_bind_node = {**_qbmm_node(), "implementation": None}
    record = {
        **pure_bind_node.pop("_native_call"),
        "node_id": pure_bind_node["node_id"],
        "typed": {
            "dtype": "bf16",
            "layout": "ND",
            "shapes": {
                "inputs": [[4, 8], [8, 16]],
                "outputs": [[4, 16]],
            },
        },
    }
    structure = _seal(
        {
            "schema_version": "mindie-model-structure/1",
            "model": {},
            "execution": {"phase": "decode"},
            "nodes": [pure_bind_node],
            "edges": [],
            "native_calls": [record],
        }
    )
    good = _control_event(
        "QuantBatchMatmulV3",
        shapes="4,8;8,16",
        dtypes="DT_BF16;DT_BF16",
        in_formats="ND;ND",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
    )
    swapped_out_for_in = _control_event(
        "QuantBatchMatmulV3",
        shapes="4,8;4,16",
        dtypes="DT_BF16;DT_BF16",
        in_formats="ND;ND",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
    )
    duplicated_in = _control_event(
        "QuantBatchMatmulV3",
        shapes="4,8;4,8",
        dtypes="DT_BF16;DT_BF16",
        in_formats="ND;ND",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
    )
    res = _ordinary_correspondences(
        structure, [good, swapped_out_for_in, duplicated_in], rank_replicas={"rank_0": "0"}
    )
    assert res[0] is not None and res[0]["basis"] == "declared_native_call_signature"
    assert res[1] is None
    assert res[2] is None

    # Even when legacy implementation.native_kinds is also present, a mismatched signature drops native_call!
    hybrid_node = _qbmm_node()
    hybrid_node.pop("_native_call")
    hybrid_struct = _seal(
        {
            "schema_version": "mindie-model-structure/1",
            "model": {},
            "execution": {"phase": "decode"},
            "nodes": [hybrid_node],
            "edges": [],
            "native_calls": [record],
        }
    )
    hybrid_res = _ordinary_correspondences(
        hybrid_struct, [good, swapped_out_for_in], rank_replicas={"rank_0": "0"}
    )
    assert hybrid_res[0]["native_call"] is not None
    assert hybrid_res[1]["signature_match"] is False
    assert hybrid_res[1]["native_call"] is None
    assert "call_ids" not in hybrid_res[1]

    # 2. Two conflicting HCCL call_ids sharing one raw alias tuple NEVER claim observed_proof!
    alias = {
        "rank_id": "rank_0",
        "logical_rank": 0,
        "global_task_id": "5",
        "stream_id": "26",
        "task_id": "17",
        "connection_id": "2",
        "device_id": "0",
        "start_ns": "1000",
        "end_ns": "2000",
        "compute_name": "AivKernel",
        "comm_name": "hcom_allGather__612_0_1",
    }
    nodes = []
    calls = []
    for idx, cid in enumerate(("a" * 64, "b" * 64)):
        nid = f"rank:0/s0.l{idx}.tp_ag"
        nodes.append(
            {
                "node_id": nid,
                "replica": 0,
                "stage": 0,
                "layer": idx,
                "block": "attention",
                "role": "tp_all_gather",
                "structure": {"kind": "collective"},
                "family": "collective",
                "recipe": "allgather",
                "contract": None,
                "implementation": {"native_kinds": ["AivKernel"], "selection": "declared"},
            }
        )
        calls.append(
            {
                "schema": "mindie-sim/native-call-binding/1",
                "call_id": cid,
                "node_id": nid,
                "op_id": f"s0.l{idx}.tp_ag",
                "family": "collective",
                "recipe": "allgather",
                "source_boundary": "hccl",
                "api": {"namespace": "hccl", "entry": "HcclAllGather"},
                "source": {"path": "hccl/ag.cc", "sha256": "f" * 64},
                "typed": {"dtype": "bf16"},
                "kernels": [{"name": "AivKernel", "role": "aiv", "evidence": "source_declared"}],
                "observed_aliases": [alias],
            }
        )
    amb_struct = _seal(
        {
            "schema_version": "mindie-model-structure/1",
            "model": {},
            "execution": {"phase": "decode"},
            "nodes": nodes,
            "edges": [],
            "native_calls": calls,
        }
    )
    ev = Event(
        rank_id="rank_0",
        rank_index=0,
        name="AivKernel",
        op_type="AivKernel",
        task_type="MIX_AIC",
        core="MIX_AIC",
        stream_id="26",
        task_id="17",
        device_id="0",
        start_ns=1000,
        end_ns=2000,
        source_kind="db",
        table="COMPUTE_TASK_INFO",
        locator={"global_task_id": "5", "connection_id": "2", "source": "/prepare-only"},
    )
    mapper = StructureMapper(
        amb_struct,
        bindings={
            "schema_version": "mindie-profile-bindings/1",
            "graph_id": amb_struct["graph_id"],
            "rank_replicas": {"rank_0": "0"},
        },
    )
    win = Window(1000, 2000, step=3)
    src = SourceRef("rank_0", 0, "db", "/prepare-only", "prepare-only", None, 1, "1", "raw", 1)
    mapper.map_window(
        Observation("rank_0", 0, win, account_window([ev], win), [ev], src, QueryStats("rank_0", "3"))
    )
    corr = mapper.sample[0]["implementation_correspondence"]
    assert corr is None or (
        corr.get("observed_proof") is not True
        and corr.get("occurrence_binding_implied") is not True
    )
    assert mapper.sample[0].get("native_call_occurrence") is None

    # 3. Same call_id across two distinct layer owners (sim v0.9.11 behavior) NEVER promotes to observed_proof!
    schema = pytest.importorskip("mindie_sim.schema.operators")
    hccl_graph = pytest.importorskip("mindie_sim.prediction.hccl_graph")
    native_binding = pytest.importorskip("mindie_sim.prediction.native_binding")
    structure_module = pytest.importorskip("mindie_sim.structure")
    two_layer_ops = [
        schema.OpSpec(
            f"s0.l{layer}.tp_all_gather",
            "allgather",
            "decode",
            0,
            layer,
            (),
            (5120,),
            (5120,),
            (5120,),
            (5120,),
            link_bytes=10240,
            dtype="bf16",
            metadata=(("group_axis", "tp"), ("collective", "allgather")),
        )
        for layer in (0, 1)
    ]
    lowered_two = list(hccl_graph.lower(tuple(two_layer_ops), SimpleNamespace(kernels={}), "bf16"))
    lowered_two = [
        native_binding.declare_native_call(
            item,
            api={"namespace": "hccl", "entry": "HcclAllGather"},
            source={"path": "hccl/all_gather.cc", "sha256": "a" * 64},
            kernels=[{"name": "AivKernel", "role": "aiv", "evidence": "source_declared"}],
            observed_aliases=[alias],
        )
        if item.family != "barrier"
        else item
        for item in lowered_two
    ]
    shared_cid_struct = structure_module.export_op_structure(
        {0: tuple(lowered_two)},
        model={},
        execution={"phase": "decode"},
        native_evidence=True,
    )
    shared_mapper = StructureMapper(
        shared_cid_struct,
        bindings={
            "schema_version": "mindie-profile-bindings/1",
            "graph_id": shared_cid_struct["graph_id"],
            "rank_replicas": {"rank_0": "0"},
        },
    )
    shared_mapper.map_window(
        Observation("rank_0", 0, win, account_window([ev], win), [ev], src, QueryStats("rank_0", "3"))
    )
    shared_corr = shared_mapper.sample[0]["implementation_correspondence"]
    assert shared_corr is None or (
        shared_corr.get("observed_proof") is not True
        and shared_corr.get("occurrence_binding_implied") is not True
        and (shared_corr.get("native_call") or {}).get("timing_owner") is None
    )
    assert shared_mapper.sample[0].get("native_call_occurrence") is None

    # 4. Incomplete dtype/format descriptors remain unresolved rather than matching MLA signature!
    mla = _mla_structure()
    for incomplete in (
        _control_event("decode_attention_fwd_grouped", dtypes="", out_dtypes="DT_BF16", task="30"),
        _control_event("decode_attention_fwd_grouped", dtypes="DT_BF16", out_dtypes="", task="31"),
        _control_event("decode_attention_fwd_grouped", in_formats="", out_formats="ND", task="32"),
        _control_event("decode_attention_fwd_grouped", in_formats="ND", out_formats="", task="33"),
    ):
        assert _ordinary_correspondences(mla, [incomplete], rank_replicas={"rank_0": "0"})[0] is None

    # 5. Single-owner HCCL occurrences evict closed raw identities across sequential windows (O(Active State))!
    single_lowered = [
        item for item in lowered_two if item.op_id.startswith("s0.l0.")
    ]
    aliases_seq = [
        {
            **alias,
            "global_task_id": str(100 + i),
            "task_id": str(200 + i),
            "start_ns": str(i * 100),
            "end_ns": str(i * 100 + 50),
        }
        for i in range(60)
    ]
    single_lowered[0] = native_binding.declare_native_call(
        single_lowered[0],
        api={"namespace": "hccl", "entry": "HcclAllGather"},
        source={"path": "hccl/all_gather.cc", "sha256": "a" * 64},
        kernels=[{"name": "AivKernel", "role": "aiv", "evidence": "source_declared"}],
        observed_aliases=aliases_seq,
    )
    seq_struct = structure_module.export_op_structure(
        {0: tuple(single_lowered)},
        model={},
        execution={"phase": "decode"},
        native_evidence=True,
    )
    seq_mapper = StructureMapper(
        seq_struct,
        bindings={
            "schema_version": "mindie-profile-bindings/1",
            "graph_id": seq_struct["graph_id"],
            "rank_replicas": {"rank_0": "0"},
        },
    )
    for i in range(60):
        w_i = Window(i * 100, i * 100 + 50, step=i)
        e_i = Event(
            rank_id="rank_0",
            rank_index=0,
            name="AivKernel",
            op_type="AivKernel",
            task_type="MIX_AIC",
            core="MIX_AIC",
            stream_id="26",
            task_id=str(200 + i),
            device_id="0",
            start_ns=i * 100,
            end_ns=i * 100 + 50,
            source_kind="db",
            table="COMPUTE_TASK_INFO",
            locator={"global_task_id": str(100 + i), "connection_id": "2", "source": "/prepare-only"},
        )
        seq_mapper.map_window(
            Observation("rank_0", 0, w_i, account_window([e_i], w_i), [e_i], src, QueryStats("rank_0", str(i)))
        )
        assert seq_mapper.sample[-1]["native_call_occurrence"] is not None
        assert len(seq_mapper.native_tracker.primary_by_raw) == 0
        assert len(seq_mapper.native_tracker.presentation_counts) == 0
