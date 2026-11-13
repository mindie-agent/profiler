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
    mapper.map_window(_obs([ev_qkv, ev_down_bare_float, attn_ev]))
    c_qkv, c_down, c_attn = [
        row["implementation_correspondence"] for row in mapper.sample
    ]
    assert c_qkv["signature_match"] is True
    assert c_qkv["native_call"]["call_id"] == calls_by_op["l0.qkv"]["call_id"]
    assert c_down["signature_match"] is True
    assert c_down["native_call"]["call_id"] == calls_by_op["l0.down"]["call_id"]
    assert c_attn["signature_match"] is True
    assert c_attn["native_call"]["call_id"] == calls_by_op["l0.attn"]["call_id"]


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
