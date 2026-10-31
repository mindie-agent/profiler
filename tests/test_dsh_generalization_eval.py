"""Regression tests for dual-stream MoE communication bounds and DSH evaluator cache/pool contracts.

[Role] Verify that dual_stream_moe_hidden_consumer requires a complete, ordered,
  dtype/shape-verified ForeachAdd -> HcPost -> HcPre -> RmsNorm chain, and that
  dsh_generalization_eval enforces parser-versioned caches and <= 4 worker bounds.
[Invariants] Missing tensor shapes, wrong widths, missing task IDs, or reversed
  HcPre/HcPost ordering must be rejected (returning None). Stale v2 caches without
  matching PARSER_IDENTITY must be invalidated.
[Timeouts & Locks] Pure in-memory unit tests (< 2s); isolated tmp_path cache root.
[Side-Effect Policy] Read-only against repository fixtures; writes only to tmp_path.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "examples" / "structure") not in sys.path:
    sys.path.insert(0, str(ROOT / "examples" / "structure"))

import dsh_generalization_eval as dsh_eval
from mindie_profiler.communication_bounds import dual_stream_moe_hidden_consumer
from mindie_profiler.decode_segmentation import _MATRICES, _Row
from mindie_profiler.events import Event, PARSER_VERSION
from mindie_profiler.normalized import shapes


def _make_row(
    op_type: str,
    start_ns: int,
    end_ns: int,
    *,
    stream_id: str = "270",
    task_id: str = "100",
    core: str = "AI_VECTOR_CORE",
    input_shapes: str = "",
    output_shapes: str = "",
    input_dtypes: str = "",
    output_dtypes: str = "",
    locator: str = "row:1",
) -> _Row:
    ev = Event(
        rank_id="0",
        rank_index=0,
        name=op_type,
        op_type=op_type,
        task_type=core,
        core=core,
        stream_id=stream_id,
        task_id=task_id,
        device_id="0",
        start_ns=start_ns,
        end_ns=end_ns,
        source_kind="kernel_details_csv",
        table="csv",
        input_shapes=input_shapes,
        output_shapes=output_shapes,
        input_dtypes=input_dtypes,
        output_dtypes=output_dtypes,
        input_formats="ND",
        output_formats="ND",
        locator={"row": locator},
    )
    return _Row(ev, shapes(ev.input_shapes), shapes(ev.output_shapes))


def _valid_dual_stream_rows() -> list[_Row]:
    return [
        _make_row(
            "MoeDistributeCombineV2",
            1_000,
            2_000,
            stream_id="270",
            task_id="1674",
            input_shapes="192,4096;4,6",
            output_shapes="4,4096",
            input_dtypes="DT_BF16;INT32",
            output_dtypes="DT_BF16",
            locator="row:combine",
        ),
        _make_row(
            "QuantBatchMatmulV3",
            1_100,
            2_100,
            stream_id="264",
            task_id="268",
            core="AI_CORE",
            input_shapes="32,256;128,16,16,32",
            output_shapes="32,4096",
            input_dtypes="INT8;INT8",
            output_dtypes="DT_BF16",
            locator="row:shared",
        ),
        _make_row(
            "hcom_allReduce_",
            2_200,
            66_000_000,
            stream_id="N/A",
            task_id="N/A",
            core="HCCL",
            locator="row:summary",
        ),
        _make_row(
            "ForeachAddList",
            2_500,
            3_000,
            stream_id="270",
            task_id="1680",
            input_shapes="32,4096;32,4096;",
            output_shapes="32,4096",
            input_dtypes="DT_BF16;DT_BF16;FLOAT",
            output_dtypes="DT_BF16",
            locator="row:add",
        ),
        _make_row(
            "HcPost",
            3_100,
            3_500,
            stream_id="270",
            task_id="1681",
            input_shapes="1,32,4096;1,32,4,4096;1,32,4;1,32,4,4",
            output_shapes="1,32,4,4096",
            input_dtypes="DT_BF16;DT_BF16;FLOAT;FLOAT",
            output_dtypes="DT_BF16",
            locator="row:hc_post",
        ),
        _make_row(
            "HcPre",
            3_600,
            4_000,
            stream_id="270",
            task_id="1682",
            input_shapes="32,4,4096;24,16384;3;24;",
            output_shapes="32,4096;32,4;32,4,4;32,4",
            input_dtypes="DT_BF16;FLOAT;FLOAT;FLOAT;DT_UNDEFINED",
            output_dtypes="DT_BF16;FLOAT;FLOAT;FLOAT",
            locator="row:hc_pre",
        ),
        _make_row(
            "RmsNorm",
            4_100,
            4_500,
            stream_id="270",
            task_id="1683",
            input_shapes="32,4096;4096",
            output_shapes="32,4096;32,1",
            input_dtypes="DT_BF16;DT_BF16",
            output_dtypes="DT_BF16;FLOAT",
            locator="row:norm",
        ),
    ]


def test_dual_stream_moe_hidden_consumer_positive_and_negative_controls():
    rows = _valid_dual_stream_rows()
    matched = dual_stream_moe_hidden_consumer(rows, 2, 6, 4096, 8, _MATRICES)
    assert matched is not None
    ev = matched["evidence"]
    assert ev["basis"] == "captured_dual_stream_moe_foreach_add_mhc_norm_chain"
    assert ev["merged_hidden_shape"] == [32, 4096]
    assert ev["mhc_stream_shape"] == [32, 4, 4096]
    assert ev["hc_post_locator"] == {"row": "row:hc_post"}
    assert ev["hc_pre_locator"] == {"row": "row:hc_pre"}

    # Negative control 1: missing HcPost/HcPre tensor shapes
    no_tensors = list(rows)
    for idx in (4, 5):
        e = replace(no_tensors[idx].event, input_shapes="", output_shapes="")
        no_tensors[idx] = _Row(e, shapes(e.input_shapes), shapes(e.output_shapes))
    assert dual_stream_moe_hidden_consumer(no_tensors, 2, 6, 4096, 8, _MATRICES) is None

    # Negative control 2: missing HcPost/HcPre task IDs
    no_tasks = list(rows)
    for idx in (4, 5):
        e = replace(no_tasks[idx].event, task_id="N/A")
        no_tasks[idx] = _Row(e, shapes(e.input_shapes), shapes(e.output_shapes))
    assert dual_stream_moe_hidden_consumer(no_tasks, 2, 6, 4096, 8, _MATRICES) is None

    # Negative control 3: wrong HcPost/HcPre tensor width
    wrong_width = list(rows)
    for idx in (4, 5):
        e = replace(wrong_width[idx].event, input_shapes="1,17", output_shapes="1,17")
        wrong_width[idx] = _Row(e, shapes(e.input_shapes), shapes(e.output_shapes))
    assert dual_stream_moe_hidden_consumer(wrong_width, 2, 6, 4096, 8, _MATRICES) is None

    # Negative control 4: reversed HcPre before HcPost
    reversed_ops = list(rows)
    for idx in (4, 5):
        e = replace(reversed_ops[idx].event, op_type="HcPre" if reversed_ops[idx].kind == "HcPost" else "HcPost")
        reversed_ops[idx] = _Row(e, shapes(e.input_shapes), shapes(e.output_shapes))
    assert dual_stream_moe_hidden_consumer(reversed_ops, 2, 6, 4096, 8, _MATRICES) is None


def test_dsh_evaluator_worker_bounds_and_parser_versioned_cache(tmp_path, monkeypatch):
    assert dsh_eval._bounded_workers(16) <= 4
    assert dsh_eval._bounded_workers(8) <= 4
    assert PARSER_VERSION in dsh_eval.PARSER_IDENTITY
    assert dsh_eval.CACHE_VERSION.startswith(f"v3:{PARSER_VERSION}:")
    assert not hasattr(dsh_eval, "trim_trailing_idle_outlier_gaps")

    csv_file = tmp_path / "kernel_details.csv"
    csv_file.write_text("Name,Type,Start Time(us),Duration(us)\n", encoding="utf-8")
    traits = {"phase": "decode", "tp": 8}
    tpl = json.loads((ROOT / "examples" / "structure" / "cases" / "decode-v4flash-a3-tp8-c4.json").read_text())
    seg = {}
    stat = csv_file.stat()
    cfg = {**dsh_eval._model_config(tpl), **seg}
    sidecars = dsh_eval._sidecar_identities(csv_file.parent)

    # Write a stale cache entry without parser_identity or with old cache_version
    stale_key = sha256(
        json.dumps(
            {
                "cache_version": dsh_eval.CACHE_VERSION,
                "parser_identity": dsh_eval.PARSER_IDENTITY,
                "path": str(csv_file.resolve()),
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "phase": traits["phase"],
                "cfg": cfg,
                "seg_opts": seg,
                "sidecars": sidecars,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    monkeypatch.setattr(dsh_eval, "CACHE_ROOT", tmp_path)
    (tmp_path / f"{stale_key}.json").write_text(
        json.dumps(
            {
                "cache_version": "v2",
                "cache_key": stale_key,
                "observed": {"forward_count": 5, "geometry_groups": [{"body_forward_span_ms": {"count": 5, "mean": 95.108}}]},
                "meta": {},
            }
        ),
        encoding="utf-8",
    )

    fresh_obs = {
        "forward_count": 5,
        "geometry_groups": [{"geometry": {"query_rows": 32}, "body_forward_span_ms": {"count": 5, "mean": 51.346}, "per_layer_ms": []}],
    }
    monkeypatch.setattr(dsh_eval, "_source", lambda *a, **kw: ([], {"kind": "csv"}))
    monkeypatch.setattr(dsh_eval, "auto_segment_decode_forwards", lambda *a, **kw: fresh_obs)
    monkeypatch.setattr(dsh_eval, "compact_observation", lambda obs: obs)

    extracted = dsh_eval.extract_or_load(csv_file, traits, tpl, seg)
    assert extracted["observed"]["geometry_groups"][0]["body_forward_span_ms"]["mean"] == 51.346
