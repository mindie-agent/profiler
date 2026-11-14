"""mindie-sim v0.9.11 multi-variant BIND1 and Golden Capture ABI matching tests.

[Role]
  Verify ``StructureMapper`` and ``native_call_signature_match`` resolve
  multi-variant ``MatMulV2`` declarations exported by ``mindie-sim v0.9.11``,
  real GLM-4.5 Golden Capture ``FusedInferAttentionScore`` optional/scalar ABI
  slots, and bare exporter dtype spellings (``FLOAT``, ``BFLOAT16``).

[Invariants]
  * One incompatible ``MatMulV2`` variant never suppresses a valid ``BIND1``
    signature match on a sibling ``MatMulV2`` variant.
  * Absent optional ``DT_UNDEFINED`` tensor slots and 0-D scalar ``""`` shape
    slots are parsed in positional lockstep with shapes and formats.
  * Real ``FLOAT`` / ``DT_FLOAT`` exporter tokens normalize identically to ``fp32``.

[Timeouts & Locks]
  In-memory ``mindie-sim`` DAG export and read-only Golden DB query (< 2s); no locks.

[Side-Effect Policy]
  Reads ``tests/fixtures/profiler_core/real_glm45`` read-only; no writes.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from mindie_profiler.accounting import account_window
from mindie_profiler.events import Event, Observation, QueryStats, SourceRef, Window
from mindie_profiler.structure_mapping import StructureMapper
from mindie_profiler.structure_native_calls import (
    event_signature,
    native_call_signature_match,
)

GLM45_DB = (
    Path(__file__).parent
    / "fixtures"
    / "profiler_core"
    / "real_glm45"
    / "rank_0"
    / "ASCEND_PROFILER_OUTPUT"
    / "ascend_pytorch_profiler_0.db"
)


def _obs(events: list[Event], rank: str = "rank_0") -> Observation:
    window = Window(0, 100_000, step=1)
    source = SourceRef(
        rank_id=rank,
        rank_index=0,
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
        rank, 0, window, account_window(events, window), events, source, QueryStats(rank, "1")
    )


def _ev(
    name: str,
    *,
    op_type: str | None = None,
    in_shapes: str,
    in_dtypes: str,
    in_formats: str = "ND;ND",
    out_shapes: str,
    out_dtypes: str,
    out_formats: str = "ND",
    idx: int = 1,
) -> Event:
    return Event(
        rank_id="rank_0",
        rank_index=0,
        name=name,
        op_type=op_type or name,
        task_type="MIX_AIC",
        core="MIX_AIC",
        stream_id="4",
        task_id=str(idx),
        device_id="0",
        start_ns=idx * 1_000,
        end_ns=idx * 1_000 + 500,
        source_kind="db",
        table="COMPUTE_TASK_INFO",
        input_shapes=in_shapes,
        input_dtypes=in_dtypes,
        input_formats=in_formats,
        output_shapes=out_shapes,
        output_dtypes=out_dtypes,
        output_formats=out_formats,
        locator={"source": "/prepare-only", "task_rowid": idx},
    )


def test_sim_v0911_multi_variant_matmul_and_real_glm45_attention_abi() -> None:
    sim_structure = pytest.importorskip("mindie_sim.structure")
    sim_ops = pytest.importorskip("mindie_sim.schema.operators")

    ops = [
        sim_ops.OpSpec(
            op_id="l0.qkv",
            family="matmul",
            phase="prefill",
            stage="prefill",
            layer=0,
            requests=("r0",),
            dtype="bf16",
            semantic_shape=(4, 16, 8),
            local_shape=(4, 16, 8),
            padded_shape=(4, 16, 8),
            launch_shape=(4, 16, 8),
            metadata={
                "native_implementation": {"native_kinds": ("MatMulV2",)},
                "native_kind": "MatMulV2",
                "native_tensor_view": {
                    "input_shape": [4, 8],
                    "weight_shape": [8, 16],
                    "output_shape": [4, 16],
                },
            },
        ),
        sim_ops.OpSpec(
            op_id="l0.down",
            family="matmul",
            phase="prefill",
            stage="prefill",
            layer=0,
            requests=("r0",),
            dtype="fp32",
            semantic_shape=(4, 8, 32),
            local_shape=(4, 8, 32),
            padded_shape=(4, 8, 32),
            launch_shape=(4, 8, 32),
            metadata={
                "native_implementation": {"native_kinds": ("MatMulV2",)},
                "native_kind": "MatMulV2",
                "native_tensor_view": {
                    "input_shape": [4, 32],
                    "weight_shape": [32, 8],
                    "output_shape": [4, 8],
                },
            },
        ),
        sim_ops.OpSpec(
            op_id="l0.attn",
            family="attention",
            phase="prefill",
            stage="prefill",
            layer=0,
            requests=("r0",),
            dtype="bf16",
            semantic_shape=(2, 12, 128),
            local_shape=(2, 12, 128),
            padded_shape=(2, 12, 128),
            launch_shape=(2, 12, 128),
            metadata={
                "native_kind": "FusedInferAttentionScore",
                "attention_tensor_view": {
                    "logical_layout": "TND",
                    "kv_storage": "contiguous",
                    "query_shape": [2, 12, 128],
                    "key_shape": [4716, 128, 128],
                    "value_shape": [4716, 128, 128],
                    "output_shape": [2, 12, 128],
                    "query_dtype": "bf16",
                    "key_dtype": "bf16",
                    "value_dtype": "bf16",
                    "output_dtype": "bf16",
                },
            },
        ),
    ]
    structure = sim_structure.export_op_structure(
        ops,
        model={"num_hidden_layers": 1},
        execution={"phase": "prefill"},
        native_evidence=True,
    )
    calls_by_op = {row["op_id"]: row for row in structure["native_calls"]}

    # Load the real FusedInferAttentionScore row directly from the GLM-4.5 Golden DB!
    con = sqlite3.connect(f"file:{GLM45_DB.resolve()}?mode=ro", uri=True)
    try:
        glm_row = con.execute(
            """
            SELECT st.value, ish.value, idt.value, ifm.value, osh.value, odt.value, ofm.value
            FROM COMPUTE_TASK_INFO c
            JOIN STRING_IDS st ON st.id = c.opType
            JOIN STRING_IDS ish ON ish.id = c.inputShapes
            JOIN STRING_IDS idt ON idt.id = c.inputDataTypes
            JOIN STRING_IDS ifm ON ifm.id = c.inputFormats
            JOIN STRING_IDS osh ON osh.id = c.outputShapes
            JOIN STRING_IDS odt ON odt.id = c.outputDataTypes
            JOIN STRING_IDS ofm ON ofm.id = c.outputFormats
            WHERE st.value = 'FusedInferAttentionScore'
            LIMIT 1
            """
        ).fetchone()
    finally:
        con.close()
    assert glm_row is not None
    attn_ev = _ev(
        glm_row[0],
        in_shapes=glm_row[1],
        in_dtypes=glm_row[2],
        in_formats=glm_row[3],
        out_shapes=glm_row[4],
        out_dtypes=glm_row[5],
        out_formats=glm_row[6],
        idx=3,
    )
    sig = event_signature(attn_ev)
    assert sig is not None
    # 7 present input tensors + 2 output slots (primary + 0D softmax_lse) == 9 aligned lanes!
    assert len(sig[0]) == len(sig[1]) == 9
    assert native_call_signature_match(calls_by_op["l0.attn"], attn_ev) is True

    # Negative control: wrong key shape on FusedInferAttentionScore is rejected.
    bad_attn = _ev(
        "FusedInferAttentionScore",
        in_shapes=glm_row[1].replace("4716,128,128", "1024,128,128"),
        in_dtypes=glm_row[2],
        in_formats=glm_row[3],
        out_shapes=glm_row[4],
        out_dtypes=glm_row[5],
        out_formats=glm_row[6],
        idx=4,
    )
    assert native_call_signature_match(calls_by_op["l0.attn"], bad_attn) is False

    # Multi-variant MatMulV2 + bare FLOAT spelling resolve their exact respective call_ids!
    ev_qkv = _ev(
        "MatMulV2",
        in_shapes="4,8;8,16",
        in_dtypes="BFLOAT16;BFLOAT16",
        out_shapes="4,16",
        out_dtypes="BFLOAT16",
        idx=1,
    )
    ev_down_bare_float = _ev(
        "MatMulV2",
        in_shapes="4,32;32,8",
        in_dtypes="FLOAT;FLOAT",
        out_shapes="4,8",
        out_dtypes="FLOAT",
        idx=2,
    )
    mapper = StructureMapper(
        structure,
        bindings={
            "schema_version": "mindie-profile-bindings/1",
            "graph_id": structure["graph_id"],
            "rank_replicas": {"rank_0": "0"},
        },
    )
    win_forward = mapper.map_window(_obs([ev_qkv, ev_down_bare_float, attn_ev]))
    c_qkv, c_down, c_attn = [
        row["implementation_correspondence"] for row in mapper.sample
    ]
    assert c_qkv["signature_match"] is True
    assert c_qkv["native_call"]["call_id"] == calls_by_op["l0.qkv"]["call_id"]
    assert c_down["signature_match"] is True
    assert c_down["native_call"]["call_id"] == calls_by_op["l0.down"]["call_id"]
    assert c_attn["signature_match"] is True
    assert c_attn["native_call"]["call_id"] == calls_by_op["l0.attn"]["call_id"]

    # Operator summary correspondence is invariant to event arrival order across multi-variant ops!
    reverse_mapper = StructureMapper(
        structure,
        bindings={
            "schema_version": "mindie-profile-bindings/1",
            "graph_id": structure["graph_id"],
            "rank_replicas": {"rank_0": "0"},
        },
    )
    win_reverse = reverse_mapper.map_window(_obs([attn_ev, ev_down_bare_float, ev_qkv]))
    assert win_forward["operators"] == win_reverse["operators"]
    ops_by_type = {row["operator_type"]: row for row in win_forward["operators"]}
    mm_corr = ops_by_type["MatMulV2"]["implementation_correspondence"]
    assert mm_corr["basis"] == "multiple_event_correspondences"
    assert mm_corr["native_call"] is None
    assert mm_corr["observed_signature"] is None
    assert mm_corr["signature_match"] is True
    assert mm_corr["variant_count"] == 2
    assert mm_corr["call_ids"] == sorted(
        [calls_by_op["l0.qkv"]["call_id"], calls_by_op["l0.down"]["call_id"]]
    )
    assert ops_by_type["FusedInferAttentionScore"]["implementation_correspondence"] == c_attn


def test_quantized_role_paired_dtype_and_c1hwncoc0_layout_rejection() -> None:
    sim_ops = pytest.importorskip("mindie_sim.schema.operators")
    sim_structure = pytest.importorskip("mindie_sim.structure")

    quant_op = sim_ops.OpSpec(
        op_id="l0.quant_proj",
        family="matmul",
        phase="prefill",
        stage="prefill",
        layer=0,
        requests=("r0",),
        dtype="bf16",
        semantic_shape=(4, 16),
        local_shape=(4, 16),
        padded_shape=(4, 16),
        launch_shape=(4, 16),
        metadata={
            "native_kind": "QuantBatchMatmulV3",
            "native_tensor_view": {
                "input_shape": [4, 8],
                "weight_shape": [8, 16],
                "output_shape": [4, 16],
                "weight_dtype": "int8",
            },
        },
    )
    structure = sim_structure.export_op_structure(
        [quant_op],
        model={"num_hidden_layers": 1},
        execution={"phase": "prefill"},
        native_evidence=True,
    )
    binding = structure["native_calls"][0]

    ev_quant_ok = _ev(
        "QuantBatchMatmulV3",
        in_shapes="4,8;8,16",
        in_dtypes="DT_BF16;DT_INT8",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
        idx=10,
    )
    ev_unquant_bad = _ev(
        "QuantBatchMatmulV3",
        in_shapes="4,8;8,16",
        in_dtypes="DT_BF16;DT_BF16",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
        idx=11,
    )
    ev_swapped_bad = _ev(
        "QuantBatchMatmulV3",
        in_shapes="4,8;8,16",
        in_dtypes="DT_INT8;DT_BF16",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
        idx=12,
    )
    ev_int8_out_bad = _ev(
        "QuantBatchMatmulV3",
        in_shapes="4,8;8,16",
        in_dtypes="DT_BF16;DT_INT8",
        out_shapes="4,16",
        out_dtypes="DT_INT8",
        idx=13,
    )
    assert native_call_signature_match(binding, ev_quant_ok) is True
    assert native_call_signature_match(binding, ev_unquant_bad) is False
    assert native_call_signature_match(binding, ev_swapped_bad) is False
    assert native_call_signature_match(binding, ev_int8_out_bad) is False

    # Positional-only inputs without role names reject missing weight_dtype and stay unresolved on mixed slots.
    positional_binding = {
        "family": "linear",
        "typed": {
            "dtype": "bf16",
            "shapes": {"inputs": [[4, 8], [8, 16]], "outputs": [[4, 16]]},
            "attrs": {"weight_dtype": "int8"},
        },
    }
    assert native_call_signature_match(positional_binding, ev_unquant_bad) is False
    assert native_call_signature_match(positional_binding, ev_quant_ok) is None

    # Contiguous layout rejects mixed-case C1HWNCoC0 after uppercase normalization.
    ev_c1hwncoc0 = _ev(
        "QuantBatchMatmulV3",
        in_shapes="4,8;8,16",
        in_dtypes="DT_BF16;DT_INT8",
        in_formats="C1HWNCoC0;ND",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
        out_formats="ND",
        idx=14,
    )
    assert native_call_signature_match(binding, ev_c1hwncoc0) is False


def test_native_call_global_tracker_retains_spanning_identities_and_fails_above_budget() -> None:
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.structure_native_calls import (
        NativeCallGlobalTracker,
        NativeCallWindowTracker,
    )

    global_tracker = NativeCallGlobalTracker(max_active=100_000)
    corr_base = {
        "basis": "observed_hccl_alias_same_call",
        "native_call": {"call_id": "a" * 64, "timing_owner": {"op_id": "tp_ar"}},
    }
    w1 = NativeCallWindowTracker(global_tracker, {"AivKernel", "hcom_allReduce"})
    first_primary = None
    for idx in range(4_097):
        ev = Event(
            rank_id="rank_0",
            rank_index=0,
            name="AivKernel",
            op_type="AivKernel",
            task_type="MIX_AIC",
            core="MIX_AIC",
            stream_id="26",
            task_id=str(idx),
            device_id="0",
            start_ns=0,
            end_ns=5_000,
            source_kind="db",
            table="COMPUTE_TASK_INFO",
            locator={"global_task_id": str(idx), "connection_id": "2"},
        )
        _, occ = w1.observe(
            ev,
            (0, 1_000),
            {**corr_base, "raw_identity": {"rank_id": "rank_0", "global_task_id": str(idx)}},
        )
        if idx == 0:
            assert occ is not None
            first_primary = occ["primary_presentation"]
    w1.finish(window_end_ns=1_000, rank_id="rank_0")
    assert len(global_tracker.primary_by_raw) == 4_097

    # Re-presenting spanning raw identity 0 in window 2 preserves presentation_index=2 and alias_of!
    w2 = NativeCallWindowTracker(global_tracker, {"AivKernel", "hcom_allReduce"})
    ev0_alias = Event(
        rank_id="rank_0",
        rank_index=0,
        name="hcom_allReduce",
        op_type="hcom_allReduce",
        task_type="COMMUNICATION",
        core="COMMUNICATION",
        stream_id="26",
        task_id="0",
        device_id="0",
        start_ns=0,
        end_ns=5_000,
        source_kind="db",
        table="COMMUNICATION_OP",
        locator={"global_task_id": "0", "connection_id": "2"},
    )
    _, occ2 = w2.observe(
        ev0_alias,
        (1_000, 2_000),
        {**corr_base, "raw_identity": {"rank_id": "rank_0", "global_task_id": "0"}},
    )
    assert occ2 is not None
    assert occ2["presentation_index"] == 2
    assert occ2["alias_of"] == first_primary
    w2.finish(window_end_ns=5_000, rank_id="rank_0")
    assert len(global_tracker.primary_by_raw) == 0

    # Exceeding max_active fails closed with ProfilerUsageError rather than silently evicting!
    small_tracker = NativeCallGlobalTracker(max_active=2)
    w_small = NativeCallWindowTracker(small_tracker, {"AivKernel"})
    for idx in range(2):
        ev = Event(
            rank_id="rank_0",
            rank_index=0,
            name="AivKernel",
            op_type="AivKernel",
            task_type="MIX_AIC",
            core="MIX_AIC",
            stream_id="26",
            task_id=str(idx),
            device_id="0",
            start_ns=0,
            end_ns=9_000,
            source_kind="db",
            table="COMPUTE_TASK_INFO",
            locator={"global_task_id": str(idx), "connection_id": "2"},
        )
        w_small.observe(ev, (0, 1_000), {**corr_base, "raw_identity": {"rank_id": "rank_0"}})
    ev_overflow = Event(
        rank_id="rank_0",
        rank_index=0,
        name="AivKernel",
        op_type="AivKernel",
        task_type="MIX_AIC",
        core="MIX_AIC",
        stream_id="26",
        task_id="99",
        device_id="0",
        start_ns=0,
        end_ns=9_000,
        source_kind="db",
        table="COMPUTE_TASK_INFO",
        locator={"global_task_id": "99", "connection_id": "2"},
    )
    with pytest.raises(ProfilerUsageError, match="max_active=2"):
        w_small.observe(ev_overflow, (0, 1_000), {**corr_base, "raw_identity": {"rank_id": "rank_0"}})


def test_attention_input_role_order_rejects_swapped_kv_and_unknown_roles() -> None:
    sim_ops = pytest.importorskip("mindie_sim.schema.operators")
    sim_structure = pytest.importorskip("mindie_sim.structure")

    attn_op = sim_ops.OpSpec(
        op_id="l0.mla_v_diff",
        family="attention",
        phase="prefill",
        stage="prefill",
        layer=0,
        requests=("r0",),
        dtype="bf16",
        semantic_shape=(4, 12, 64),
        local_shape=(4, 12, 64),
        padded_shape=(4, 12, 64),
        launch_shape=(4, 12, 64),
        metadata={
            "native_kind": "FusedInferAttentionScore",
            "attention_tensor_view": {
                "logical_layout": "TND",
                "kv_storage": "contiguous",
                "query_shape": [4, 12, 128],
                "key_shape": [4, 12, 128],
                "value_shape": [4, 12, 64],
                "output_shape": [4, 12, 64],
                "query_dtype": "bf16",
                "key_dtype": "bf16",
                "value_dtype": "bf16",
                "output_dtype": "bf16",
            },
        },
    )
    structure = sim_structure.export_op_structure(
        [attn_op],
        model={"num_hidden_layers": 1},
        execution={"phase": "prefill"},
        native_evidence=True,
    )
    binding = structure["native_calls"][0]
    ev_ordered = _ev(
        "FusedInferAttentionScore",
        in_shapes="4,12,128;4,12,128;4,12,64;1,4",
        in_dtypes="DT_BF16;DT_BF16;DT_BF16;DT_INT32",
        in_formats="ND;ND;ND;ND",
        out_shapes="4,12,64",
        out_dtypes="DT_BF16",
        idx=20,
    )
    ev_swapped_kv = _ev(
        "FusedInferAttentionScore",
        in_shapes="4,12,128;4,12,64;4,12,128;1,4",
        in_dtypes="DT_BF16;DT_BF16;DT_BF16;DT_INT32",
        in_formats="ND;ND;ND;ND",
        out_shapes="4,12,64",
        out_dtypes="DT_BF16",
        idx=21,
    )
    assert native_call_signature_match(binding, ev_ordered) is True
    assert native_call_signature_match(binding, ev_swapped_kv) is False

    mapper = StructureMapper(
        structure,
        bindings={
            "schema_version": "mindie-profile-bindings/1",
            "graph_id": structure["graph_id"],
            "rank_replicas": {"rank_0": "0"},
        },
    )
    mapper.map_window(_obs([ev_ordered, ev_swapped_kv]))
    c_ok, c_swapped = [row["implementation_correspondence"] for row in mapper.sample]
    assert c_ok["signature_match"] is True
    assert c_ok["basis"] == "declared_native_call_signature"
    assert c_ok["native_call"]["call_id"] == binding["call_id"]
    assert c_swapped["signature_match"] is False
    assert c_swapped["basis"] == "declared_native_implementation"
    assert c_swapped["native_call"] is None

    # Unknown role names without established slot order resolve to None, never True.
    unknown_roles = {
        "family": "custom",
        "typed": {
            "dtype": "bf16",
            "shapes": {"alpha_slot": [4, 8], "beta_slot": [8, 16], "output": [4, 16]},
        },
    }
    ev_ab = _ev(
        "CustomOp",
        in_shapes="4,8;8,16",
        in_dtypes="DT_BF16;DT_BF16",
        out_shapes="4,16",
        out_dtypes="DT_BF16",
        idx=22,
    )
    assert native_call_signature_match(unknown_roles, ev_ab) is None


def test_malformed_or_dangling_native_calls_fail_closed() -> None:
    import copy
    from mindie_sim import structure as sim_structure
    from mindie_sim.schema import operators as sim_ops
    from mindie_profiler.events import ProfilerUsageError

    op = sim_ops.OpSpec(
        op_id="s0.l0.q_proj",
        family="matmul",
        phase="prefill",
        stage="prefill",
        layer=0,
        requests=("r0",),
        semantic_shape=(4, 16),
        local_shape=(4, 16),
        padded_shape=(4, 16),
        launch_shape=(4, 16),
        dtype="bf16",
        metadata={
            "native_call": {
                "schema": "mindie-sim/native-call-binding/1",
                "call_id": "e" * 64,
                "op_id": "s0.l0.q_proj",
                "family": "matmul",
                "recipe": "qbmm",
                "source_boundary": "atb",
                "api": {"namespace": "aclnn", "entry": "QuantBatchMatmulV3"},
                "source": {"path": "ops/qbmm.cpp", "sha256": "f" * 64},
                "typed": {"dtype": "bf16", "inputs": [[4, 8], [8, 16]], "outputs": [[4, 16]]},
                "kernels": [{"name": "QuantBatchMatmulV3", "role": "aic", "evidence": "source_declared"}],
            }
        },
    )
    base = sim_structure.export_op_structure(
        [op], model={"num_hidden_layers": 1}, execution={"phase": "prefill"}, native_evidence=True
    )
    binds = {
        "schema_version": "mindie-profile-bindings/1",
        "graph_id": base["graph_id"],
        "rank_replicas": {"rank_0": "0"},
    }
    assert len(StructureMapper(copy.deepcopy(base), bindings=binds).target_index.native_bindings) == 1

    bad_seq = copy.deepcopy(base)
    bad_seq["native_calls"] = "not-a-sequence"
    with pytest.raises(ProfilerUsageError, match="native_calls"):
        StructureMapper(bad_seq, bindings=binds)

    bad_item = copy.deepcopy(base)
    bad_item["native_calls"].append("malformed-binding")
    with pytest.raises(ProfilerUsageError, match="native_calls"):
        StructureMapper(bad_item, bindings=binds)

    bad_node = copy.deepcopy(base)
    bad_node["native_calls"][0]["node_id"] = "missing-semantic-node"
    with pytest.raises(ProfilerUsageError, match="unknown node_id"):
        StructureMapper(bad_node, bindings=binds)

    bad_cid = copy.deepcopy(base)
    bad_cid["native_calls"][0]["call_id"] = ""
    with pytest.raises(ProfilerUsageError, match="call_id"):
        StructureMapper(bad_cid, bindings=binds)

    dup_conflict = copy.deepcopy(base)
    other = copy.deepcopy(base["native_calls"][0])
    other["call_id"] = "9" * 64
    dup_conflict["native_calls"].append(other)
    with pytest.raises(ProfilerUsageError, match="conflicting bindings"):
        StructureMapper(dup_conflict, bindings=binds)


def test_explicitly_declared_operands_are_never_optional() -> None:
    from mindie_sim.prediction.native_binding import bind_native_call, validate_invocation
    from mindie_sim.schema.common import ModelingError
    from mindie_sim.schema import operators as sim_ops
    from mindie_sim import structure as sim_structure

    biased_op = sim_ops.OpSpec(
        op_id="l0.biased_proj",
        family="matmul",
        phase="prefill",
        stage="prefill",
        layer=0,
        requests=("r0",),
        dtype="bf16",
        semantic_shape=(4, 16, 8),
        local_shape=(4, 16, 8),
        padded_shape=(4, 16, 8),
        launch_shape=(4, 16, 8),
        metadata={
            "native_kind": "MatMulV2",
            "native_tensor_view": {
                "input_shape": [4, 8],
                "weight_shape": [8, 16],
                "bias_shape": [16],
                "output_shape": [4, 16],
            },
        },
    )
    unbiased_op = sim_ops.OpSpec(
        op_id="l0.unbiased_proj",
        family="matmul",
        phase="prefill",
        stage="prefill",
        layer=0,
        requests=("r0",),
        dtype="bf16",
        semantic_shape=(4, 16, 8),
        local_shape=(4, 16, 8),
        padded_shape=(4, 16, 8),
        launch_shape=(4, 16, 8),
        metadata={
            "native_kind": "MatMulV2",
            "native_tensor_view": {
                "input_shape": [4, 8],
                "weight_shape": [8, 16],
                "output_shape": [4, 16],
            },
        },
    )
    sim_binding = bind_native_call(biased_op)
    with pytest.raises(ModelingError, match="native_call_invocation_missing_fields:bias"):
        validate_invocation(
            sim_binding,
            {
                "dtype": "bf16",
                "layout": "contiguous",
                "shapes": {
                    "input": [4, 8],
                    "weight": [8, 16],
                    "output": [4, 16],
                    "local": [4, 16, 8],
                    "padded": [4, 16, 8],
                    "launch": [4, 16, 8],
                },
                "attrs": {},
            },
        )

    exported = sim_structure.export_op_structure(
        [biased_op, unbiased_op],
        model={"num_hidden_layers": 1},
        execution={"phase": "prefill"},
        native_evidence=True,
    )
    by_op = {row["op_id"]: row for row in exported["native_calls"]}
    ev_no_bias = _ev("MatMulV2", in_shapes="4,8;8,16", in_dtypes="DT_BF16;DT_BF16", out_shapes="4,16", out_dtypes="DT_BF16", idx=30)
    ev_with_bias = _ev("MatMulV2", in_shapes="4,8;8,16;16", in_dtypes="DT_BF16;DT_BF16;DT_BF16", in_formats="ND;ND;ND", out_shapes="4,16", out_dtypes="DT_BF16", idx=31)
    assert native_call_signature_match(by_op["l0.biased_proj"], ev_no_bias) is False
    assert native_call_signature_match(by_op["l0.biased_proj"], ev_with_bias) is True
    assert native_call_signature_match(by_op["l0.unbiased_proj"], ev_no_bias) is True
    assert native_call_signature_match(by_op["l0.unbiased_proj"], ev_with_bias) is False

    # Declared residual, scale, group_list, and indices also reject missing operands.
    for extra_role, extra_shape, extra_attrs in (
        ("residual", [4, 8], {}),
        ("scale", [16], {"scale_dtype": "fp32"}),
        ("group_list", [1], {"group_list_dtype": "int64"}),
        ("indices", [4, 128], {"index_dtype": "int32"}),
    ):
        decl = {
            "family": "attention" if extra_role == "indices" else "matmul",
            "typed": {
                "dtype": "bf16",
                "shapes": {"input": [4, 8], "weight": [8, 16], extra_role: extra_shape, "output": [4, 16]},
                "attrs": extra_attrs,
            },
        }
        assert native_call_signature_match(decl, ev_no_bias) is False
