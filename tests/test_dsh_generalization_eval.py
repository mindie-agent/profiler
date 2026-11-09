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

import pytest

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


def test_hardware_uses_real_path_components_not_slash_folding():
    posix_literal = (
        Path("/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/qwen36_tp4")
        / r"foo\a3\cell"
        / "kernel_details.csv"
    )
    posix_traits = dsh_eval.parse_capture_traits(posix_literal)
    assert posix_traits["hw"] == "a5"
    assert posix_traits["tp"] == 4

    later_a3 = Path(
        "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/qwen36_tp4/a3/kernel_details.csv"
    )
    later_traits = dsh_eval.parse_capture_traits(later_a3)
    assert later_traits["hw"] == "a5"
    assert later_traits["tp"] == 4

    assert dsh_eval._hardware_from_capture_path(
        r"\\a3\share\mindie-sim-data\a5\heldout_engine_20261030\qwen36_tp4\cell\kernel_details.csv"
    ) == "a5"
    assert dsh_eval._hardware_from_capture_path(
        r"C:\Volumes\data\mindie-sim-data\a5\heldout_engine_20261030\qwen36_tp4\cell\kernel_details.csv"
    ) == "a5"
    assert dsh_eval._hardware_from_capture_path(
        r"C:\Volumes\data\mindie-sim-data\a3\heldout_engine_20261030\qwen36_tp4\cell\kernel_details.csv"
    ) == "a3"
    with pytest.raises(ValueError, match="ambiguous hardware"):
        dsh_eval._hardware_from_capture_path("/tmp/a5/other/a3/qwen36_tp4/kernel_details.csv")

    posix_unc_str = (
        "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/qwen36_tp4/"
        r"\\literal/kernel_details.csv"
    )
    assert r"\\literal" in dsh_eval._path_dir_components(posix_unc_str)
    assert dsh_eval._hardware_from_capture_path(posix_unc_str) == "a5"
    posix_unc_lookalike = (
        Path("/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/qwen36_tp4")
        / r"\\literal"
        / "kernel_details.csv"
    )
    # Windows pathlib treats a "\\literal" join as UNC and drops the POSIX parent.
    # The string form above is the portable invariant; Path join is POSIX-only.
    if "a5" in posix_unc_lookalike.as_posix():
        assert r"\\literal" in dsh_eval._path_dir_components(posix_unc_lookalike)
        assert dsh_eval.parse_capture_traits(posix_unc_lookalike)["hw"] == "a5"

    with pytest.raises(ValueError, match="ambiguous hardware"):
        dsh_eval._hardware_from_capture_path(
            "/tmp/a5/captures/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/"
            "qwen36_tp4/cell/kernel_details.csv"
        )


def test_parse_capture_traits_rejects_unknown_family_missing_tp_and_hardware():
    unknown = Path("/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/mystery_suite/cell_c4/kernel_details.csv")
    with pytest.raises(ValueError, match="unrecognized model family"):
        dsh_eval.parse_capture_traits(unknown)

    missing_tp = Path(
        "/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/qwen36_graph/cell_c4/kernel_details.csv"
    )
    with pytest.raises(ValueError, match="missing tp token"):
        dsh_eval.parse_capture_traits(missing_tp)

    no_hw = Path("/tmp/other/qwen36_tp4/kernel_details.csv")
    with pytest.raises(ValueError, match="unrecognized hardware"):
        dsh_eval.parse_capture_traits(no_hw)


def test_parse_capture_traits_reads_path_topology_and_glm_documented_tp16():
    path = Path(
        "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/"
        "qwen35_tp4_dp2_ep8/qwen3_5_tp4_64k_c8/kernel_details.csv"
    )
    traits = dsh_eval.parse_capture_traits(path)
    assert traits["hw"] == "a5"
    assert traits["family"] == "qwen3.5-35b-a3b"
    assert traits["tp"] == 4
    assert traits["dp"] == 2
    assert traits["ep"] == 8
    assert traits["context_tokens"] == 65536
    assert traits["concurrency"] == 8

    glm = Path(
        "/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/"
        "glm5_3_flash_static/glm53flash_c10/kernel_details.csv"
    )
    glm_traits = dsh_eval.parse_capture_traits(glm)
    assert glm_traits["family"] == "glm-5.3-flash"
    assert glm_traits["tp"] == 16
    assert glm_traits["ep"] == 16
    assert glm_traits["hw"] == "a3"

    mtp_over_suite = Path(
        "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/"
        "qwen36_tp8/qwen3_6_mtp1_c4/kernel_details.csv"
    )
    mtp_traits = dsh_eval.parse_capture_traits(mtp_over_suite)
    assert mtp_traits["tp"] == 8
    assert mtp_traits["spec_tokens"] == 1
    assert mtp_traits["family"] == "qwen3.6-27b"

    forged_mtp_tp = Path(
        "/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/"
        "qwen36_graph/qwen3_6_mtp3_c4/kernel_details.csv"
    )
    with pytest.raises(ValueError, match="missing tp token"):
        dsh_eval.parse_capture_traits(forged_mtp_tp)

    heldout_eager = Path(
        "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/"
        "qwen36_eager/cell_c4/kernel_details.csv"
    )
    eager_traits = dsh_eval.parse_capture_traits(heldout_eager)
    assert eager_traits["is_eager"] is True
    assert eager_traits["family"] == "qwen3.6-27b"
    assert eager_traits["tp"] is None
    assert eager_traits["hw"] == "a5"

    top_level_eager = Path(
        "/Volumes/data/mindie-sim-data/a5/"
        "qwen3_5_35b_a3b_w8a8_mtp_high_conc_decode_tpot10ms_c32_20261030/kernel_details.csv"
    )
    top_traits = dsh_eval.parse_capture_traits(top_level_eager)
    assert top_traits["is_eager"] is True
    assert top_traits["family"] == "qwen3.5-35b-a3b"
    assert top_traits["tp"] is None

    tp4x = Path(
        "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/"
        "qwen36_tp4x/cell_c4/kernel_details.csv"
    )
    with pytest.raises(ValueError, match="missing tp token"):
        dsh_eval.parse_capture_traits(tp4x)


def test_compact_tp4dp4_is_cell_topology_not_missing_or_suite_tp():
    registered = Path(
        "/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/"
        "dsv41_tp4dp4_128k_decode_20261030/prof/decode_128k_in126k_out3k_c12/kernel_details.csv"
    )
    traits = dsh_eval.parse_capture_traits(registered)
    assert traits["family"] == "deepseek-v4.1"
    assert (traits["tp"], traits["dp"], traits["ep"]) == (4, 4, 16)

    cell_overrides_suite = Path(
        "/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/"
        "dsv41_tp8/tp4dp4_ep16_c4/kernel_details.csv"
    )
    cell_traits = dsh_eval.parse_capture_traits(cell_overrides_suite)
    assert cell_traits["family"] == "deepseek-v4.1"
    assert (cell_traits["tp"], cell_traits["dp"], cell_traits["ep"]) == (4, 4, 16)


def test_inventory_skips_registered_kimi_and_unknown_family_eager_before_topology():
    cases = json.loads((ROOT / "examples" / "structure" / "cases.json").read_text())["cases"]
    kimi = next(
        c for c in cases
        if (c.get("source") or {}).get("path", "").endswith(
            "kimi_k3_w4a8_4layer_tp8_high_conc_decode_c4_20261030/ranks/tp0/kernel_details.csv.gz"
        )
    )
    reg_by_path = {
        Path(c["source"]["path"]).resolve(): c
        for c in cases
        if c.get("source", {}).get("path") and c.get("supported_scopes") != ["engine"]
    }
    kimi_path = Path(kimi["source"]["path"]).resolve()
    bucket, traits = dsh_eval.inventory_capture(kimi_path, reg_by_path)
    assert bucket == "registered"
    assert traits is None

    unknown_eager = Path(
        "/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030/"
        "mystery_eager/cell_c4/kernel_details.csv"
    )
    eager_bucket, eager_traits = dsh_eval.inventory_capture(unknown_eager, {})
    assert eager_bucket == "eager"
    assert eager_traits["is_eager"] is True
    assert eager_traits["family"] is None
    assert eager_traits["tp"] is None

    unknown_heldout = Path(
        "/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030/mystery_suite/cell_c4/kernel_details.csv"
    )
    with pytest.raises(ValueError, match="unrecognized model family"):
        dsh_eval.inventory_capture(unknown_heldout, {})


def test_extract_or_load_does_not_turn_timeout_or_parse_errors_into_empty_geometry(tmp_path, monkeypatch):
    csv_file = tmp_path / "kernel_details.csv"
    csv_file.write_text("Name,Type,Start Time(us),Duration(us)\n", encoding="utf-8")
    traits = {"phase": "decode", "tp": 8}
    tpl = json.loads((ROOT / "examples" / "structure" / "cases" / "decode-v4flash-a3-tp8-c4.json").read_text())
    monkeypatch.setattr(dsh_eval, "CACHE_ROOT", tmp_path)
    monkeypatch.setattr(dsh_eval, "capture_metadata", lambda _path: {"context_evidence": None, "client": None})

    monkeypatch.setattr(dsh_eval, "_source", lambda *a, **kw: (_ for _ in ()).throw(TimeoutError("csv_read_deadline")))
    with pytest.raises(TimeoutError, match="csv_read_deadline"):
        dsh_eval.extract_or_load(csv_file, traits, tpl, {})

    monkeypatch.setattr(dsh_eval, "_source", lambda *a, **kw: (_ for _ in ()).throw(ValueError("malformed kernel row")))
    with pytest.raises(ValueError, match="malformed kernel row"):
        dsh_eval.extract_or_load(csv_file, traits, tpl, {})

    stat = csv_file.stat()
    cfg = {**dsh_eval._model_config(tpl), **{}}
    sidecars = dsh_eval._sidecar_identities(csv_file.parent)
    cache_key = sha256(
        json.dumps(
            {
                "cache_version": dsh_eval.CACHE_VERSION,
                "parser_identity": dsh_eval.PARSER_IDENTITY,
                "path": str(csv_file.resolve()),
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "phase": traits["phase"],
                "cfg": cfg,
                "seg_opts": {},
                "sidecars": sidecars,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    cache_path = tmp_path / f"{cache_key}.json"
    cache_path.write_text("{}\n", encoding="utf-8")
    original_read = Path.read_text

    def read_text(self, *args, **kwargs):
        if self == cache_path:
            raise TimeoutError("cache_read_deadline")
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    with pytest.raises(TimeoutError, match="cache_read_deadline"):
        dsh_eval.extract_or_load(csv_file, traits, tpl, {})
