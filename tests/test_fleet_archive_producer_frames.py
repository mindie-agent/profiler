"""Identified attention declarations are not a repeated step list.

A paged cache leading is capacity. It is not logical K, and a receipt-window
count does not have to match before the declaration is kept.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_STRUCTURE = ROOT / "examples" / "structure"
if str(_STRUCTURE) not in sys.path:
    sys.path.insert(0, str(_STRUCTURE))

import fleet_archive_producer as producer  # noqa: E402

_HEADER = (
    "Name,Type,Start Time(us),Input Shapes,Input Data Types,Input Formats,"
    "Output Shapes,Output Data Types,Output Formats,Device_id,Task ID\n"
)
_MLA = (
    "1,4,1,512;5716,1,128,512;5716,1,128,512;1;1,1280;1,4,1,64;5716,1,128,64",
    "DT_BF16;DT_BF16;DT_BF16;INT64;INT32;DT_BF16;DT_BF16",
    "ND;ND;ND;ND;ND;ND;ND",
    "4,1,1,512;",
    "DT_BF16;FLOAT",
    "ND;ND",
)


def _row(shape, dtypes, formats, out_shape, out_dtypes, out_formats, stamp, task, device="4") -> str:
    name = "aclnnFusedInferAttentionScoreV4_FusedInferAttentionScore_FusedInferAttentionScore"
    return (
        f"{name},FusedInferAttentionScore,{stamp},\"{shape}\",{dtypes},{formats},"
        f"\"{out_shape}\",{out_dtypes},{out_formats},{device},{task}\n"
    )


def _siblings(source: Path, *, layers: int, spec_k: int = 1) -> None:
    (source.parent / "meta.env").write_text(
        f"NUM_LAYERS={layers}\nSPEC_K={spec_k}\nCONCURRENCY=1\nINPUT_LEN=8\nOUTPUT_LEN=4\n",
        encoding="utf-8",
    )
    (source.parent / "benchmark_summary.json").write_text(json.dumps({
        "summary": {
            "concurrency": 1, "token_exact": True,
            "prefix": {"cached_tokens": 0, "hits": 0, "queries": 0},
            "profile": {"start_profile_epoch": 100.0, "stop_profile_epoch": 200.0},
        },
        "requests": [{
            "idx": 0, "prompt_tokens": 8, "completion_tokens": 4, "ok": True,
            "chunk_epochs": [10.0],
        }],
    }), encoding="utf-8")


def _declare(source: Path, windows: list[dict] | None):
    producer.clear_producer_caches()
    projections = [{"phase": "decode", "receipt_windows": windows or []}]
    return producer.producer_declaration(source, projections, phase="decode")


def test_repeated_paged_mla_shape_is_one_declaration(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    stamps = (50_000_000, 60_000_000, 150_000_000, 160_000_000, 250_000_000, 260_000_000)
    tasks = ("39", "77", "39", "77", "39", "77")
    text = _HEADER + "".join(
        _row(*_MLA, stamp, task) for stamp, task in zip(stamps, tasks)
    )
    source.write_text(text, encoding="utf-8")
    _siblings(source, layers=2, spec_k=1)
    windows = [
        {"forward_id": f"auto:{index}", "phase": "decode", "rank_id": "", "device_id": "4", "query_rows": 1}
        for index in range(3)
    ]
    declared = _declare(source, windows)
    frames = declared["frames"]
    assert len(frames) == 1
    frame = frames[0]
    assert frame["schedule_role"] == "model_argument_identity"
    assert frame["query_rows"] == 1
    assert frame["query_shape"] == [1, 4, 1, 512]
    assert frame["context_tokens"] is None
    assert frame["logical_context_tokens"] is None
    assert frame["cache_capacity_pages"] == 5716
    assert frame["cache_capacity_pages"] != frame["context_tokens"]
    assert frame["block_table_shape"] == [1, 1280]
    assert frame["block_table_columns_are_capacity"] is True
    assert frame["key_tensor_tokens"] is None
    assert frame["observed_call_count"] == 6
    assert frame["forward_id"] is None
    assert "receipt_forward_id" not in frame
    assert frame["device_id"] == "4"
    assert frame["rank_id"] is None
    assert frame["sequences_per_replica"] == 1
    assert frame["query_batch"] == 1
    assert frame["clock_class_counts"] == {
        "before_profile_window": 2, "inside_profile_window": 2, "after_profile_window": 2,
    }
    assert frame["layer_cycle"] == {
        "source": "kernel_task_id_file_order", "num_layers": 2, "proven": True, "closure_count": 3,
    }
    assert declared["attention_shapes"]["basis"] == "fia_native_tensor_abi_streamed"
    assert declared["attention_shapes"]["logical_kv_rows"] is None
    assert declared["attention_shapes"]["cache_capacity_pages"] == [5716]
    assert "kv_rows" not in declared["attention_shapes"]
    assert len(declared["receipt_windows"]) == 3
    assert declared["window_fields"]["unpaired_receipt_window_count"] == 3
    assert declared["window_fields"]["identified_declaration_count"] == 1
    assert declared["window_fields"]["count_mismatch_rejects_declaration"] is False
    assert not any("disagrees_with_frames" in note for note in declared["notes"])
    assert not any(note.startswith("conflict:") for note in declared["notes"])


def test_missing_receipt_windows_do_not_block_the_declaration(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(_HEADER + _row(*_MLA, 150_000_000, "39"), encoding="utf-8")
    _siblings(source, layers=27)
    declared = _declare(source, None)
    assert len(declared["frames"]) == 1
    assert declared["frames"][0]["context_tokens"] is None
    assert declared["frames"][0]["layer_cycle"]["proven"] is False
    assert declared["receipt_windows"] in (None, [])
    assert not any("disagrees_with_frames" in note for note in declared["notes"])


def test_large_source_keeps_the_abi_map_and_does_not_use_the_blind_gate(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    body = _HEADER + _row(*_MLA, 150_000_000, "39")
    source.write_text(body + ("\n" * (8 * 1024 * 1024)), encoding="utf-8")
    assert source.stat().st_size > 8 * 1024 * 1024
    _siblings(source, layers=27)
    declared = _declare(source, None)
    assert len(declared["frames"]) == 1
    assert declared["frames"][0]["query_rows"] == 1
    assert declared["frames"][0]["cache_capacity_pages"] == 5716
    assert declared["attention_shapes"]["basis"] == "fia_native_tensor_abi_streamed"
    assert "attention_shapes_not_scanned_source_larger_than_8mib" not in declared["notes"]


def test_unidentified_layout_stays_empty_and_names_the_scan(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    shape = "8192,4,128;8192,4,128;8192,4,128;2048,2048;1;1;8192,4,64;8192,4,64"
    dtypes = "DT_BF16;DT_BF16;DT_BF16;INT8;INT64;INT64;DT_BF16;DT_BF16"
    formats = "ND;ND;ND;ND;ND;ND;ND;ND"
    out_shape = "8192,4,128;8192,4,1"
    out_dtypes = "DT_BF16;FLOAT"
    out_formats = "ND;ND"
    body = _HEADER + _row(shape, dtypes, formats, out_shape, out_dtypes, out_formats, 150_000_000, "1")
    source.write_text(body + ("\n" * (8 * 1024 * 1024)), encoding="utf-8")
    _siblings(source, layers=27)
    declared = _declare(source, [
        {"forward_id": "auto:0", "phase": "prefill", "rank_id": "", "device_id": "4", "query_rows": 8192},
    ])
    assert declared["frames"] == []
    assert declared["attention_shapes"] is None
    assert "attention_shapes_streamed_abi_not_identified" in declared["notes"]
    assert "attention_shapes_not_scanned_source_larger_than_8mib" not in declared["notes"]
    assert "receipt_window_count_1_disagrees_with_frames_0" in declared["notes"]
    assert len(declared["receipt_windows"]) == 1


def test_no_attention_rows_are_named_without_the_size_gate(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(_HEADER + "Add,Add,1,1,INT32,ND,1,INT32,ND,0,1\n" + ("\n" * (8 * 1024 * 1024)), encoding="utf-8")
    _siblings(source, layers=2)
    declared = _declare(source, None)
    assert declared["frames"] == []
    assert "no_fused_infer_attention_rows" in declared["notes"]
    assert "attention_shapes_not_scanned_source_larger_than_8mib" not in declared["notes"]


def test_batched_mla_query_batch_is_not_a_repeated_context(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    shape = "4,4,1,512;5716,1,128,512;5716,1,128,512;4;4,1280;4,4,1,64;5716,1,128,64"
    out_shape = "4,4,1,512;"
    source.write_text(
        _HEADER + _row(shape, _MLA[1], _MLA[2], out_shape, _MLA[4], _MLA[5], 150_000_000, "39"),
        encoding="utf-8",
    )
    _siblings(source, layers=2)
    declared = _declare(source, None)
    frame = declared["frames"][0]
    assert len(declared["frames"]) == 1
    assert frame["query_rows"] == 1
    assert frame["query_batch"] == 4
    assert frame["sequences_per_replica"] == 4
    assert frame["context_tokens"] is None
    assert frame["cache_capacity_pages"] == 5716
    assert frame["observed_call_count"] == 1


def _dense(query: int, key_tokens: int) -> tuple[str, str, str, str, str, str]:
    shape = f"{query},4,256;{key_tokens},1,256;{key_tokens},1,256;2048,2048;1;1"
    dtypes = "DT_BF16;DT_BF16;DT_BF16;DT_INT8;DT_INT64;DT_INT64"
    formats = "ND;ND;ND;ND;ND;ND"
    out_shape = f"{query},4,256;1"
    return shape, dtypes, formats, out_shape, "DT_BF16;FLOAT", "ND;ND"


def _paged(query: int, pages: int) -> tuple[str, str, str, str, str, str]:
    shape = f"{query},4,256;{pages},128,256;{pages},128,256;;;;1,3200"
    dtypes = "DT_BF16;DT_BF16;DT_BF16;DT_UNDEFINED;DT_UNDEFINED;DT_UNDEFINED;DT_INT32"
    formats = "ND;ND;ND;NULL;NULL;NULL;ND"
    out_shape = f"{query},4,256;1"
    return shape, dtypes, formats, out_shape, "DT_BF16;FLOAT", "ND;ND"


def _prefill(source: Path, windows: list[dict], *, prompt: int | None, cmd: str | None, prefix_len: int | None = None):
    lines = ["INPUT_LEN=" + str(prompt)] if prompt is not None else []
    if prefix_len is not None:
        lines.append(f"PREFIX_LEN={prefix_len}")
    lines.append("MODE=prefill")
    (source.parent / "meta.env").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if cmd is not None:
        (source.parent / "cmd.sh").write_text(cmd + "\n", encoding="utf-8")
    producer.clear_producer_caches()
    return producer.producer_declaration(source, [{"phase": "prefill", "receipt_windows": windows}], phase="prefill")


def _window(forward_id: str, query: int, device: str = "4", rank: str = "") -> dict:
    return {"forward_id": forward_id, "phase": "prefill", "rank_id": rank, "device_id": device, "query_rows": query}


def test_dense_key_axis_closes_context_zero_and_paged_capacity_does_not(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(
        _HEADER
        + _row(*_dense(3840, 3840), 10, "11654")
        + _row(*_dense(3840, 3840), 20, "12171")
        + _row(*_paged(256, 312190), 30, "12786")
        + _row(*_paged(256, 312190), 40, "13279"),
        encoding="utf-8",
    )
    declared = _prefill(
        source,
        [_window("prefill:0", 3840), _window("prefill:1", 256)],
        prompt=4096,
        cmd="vllm serve model --enable-prefix-caching --enable-chunked-prefill --tensor-parallel-size 4",
        prefix_len=0,
    )
    frames = declared["frames"]
    assert [(item["query_rows"], item["context_tokens"], item["kv_end"]) for item in frames] == [
        (3840, 0, 3840), (256, 3840, 4096),
    ]
    assert frames[0]["basis"] == "dense_key_token_axis_equals_new_query"
    assert frames[0]["schedule_role"] == "prefill_physical_step"
    assert frames[0]["key_tensor_tokens"] == 3840
    assert frames[0]["forward_id"] == "prefill:0"
    assert frames[0]["device_id"] == "4"
    assert frames[0]["rank_id"] is None
    assert frames[1]["basis"] == "prior_closed_kv_end_file_order_paged_capacity_not_context"
    assert frames[1]["cache_capacity_pages"] == 312190
    assert frames[1]["context_tokens"] != frames[1]["cache_capacity_pages"]
    assert frames[1]["block_table_shape"] == [1, 3200]
    assert frames[1]["forward_id"] == "prefill:1"
    assert declared["launch"]["enable_prefix_caching"] is True
    assert "prefix_caching_enabled_context_taken_from_key_or_prior_kv" in declared["notes"]
    assert "paged_cache_capacity_not_used_as_context" in declared["notes"]
    assert "receipt_rank_id_empty_device_forward_linked" in declared["notes"]
    assert declared["attention_shapes"]["logical_kv_rows"] is None
    assert 312190 not in (frames[0]["context_tokens"], frames[1]["context_tokens"])


def test_absent_or_enabled_prefix_flag_does_not_invent_cached_zero(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(_HEADER + _row(*_paged(1024, 99999), 10, "1"), encoding="utf-8")
    absent = _prefill(source, [_window("prefill:0", 1024)], prompt=1024, cmd="vllm serve model --tensor-parallel-size 4", prefix_len=0)
    assert absent["launch"]["enable_prefix_caching"] is None
    assert absent["frames"][0]["schedule_role"] == "model_argument_identity"
    assert absent["frames"][0]["context_tokens"] is None
    assert absent["frames"][0]["query_rows"] == 1024
    assert absent["frames"][0]["cache_capacity_pages"] == 99999
    enabled = _prefill(
        source, [_window("prefill:0", 1024)], prompt=1024,
        cmd="vllm serve model --enable-prefix-caching", prefix_len=0,
    )
    assert enabled["launch"]["enable_prefix_caching"] is True
    assert enabled["frames"][0]["context_tokens"] is None
    assert enabled["frames"][0]["cache_capacity_pages"] == 99999
    assert "launch_prefix_caching_explicitly_disabled" not in [item.get("basis") for item in enabled["frames"]]


def test_explicit_prefix_disable_closes_first_paged_query_at_context_zero(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(_HEADER + _row(*_paged(1024, 99999), 10, "1"), encoding="utf-8")
    declared = _prefill(
        source, [_window("prefill:0", 1024, rank="0")], prompt=1024,
        cmd="vllm serve model --no-enable-prefix-caching --tensor-parallel-size 4",
    )
    frame = declared["frames"][0]
    assert declared["launch"]["enable_prefix_caching"] is False
    assert frame["schedule_role"] == "prefill_physical_step"
    assert frame["query_rows"] == 1024
    assert frame["context_tokens"] == 0
    assert frame["kv_end"] == 1024
    assert frame["basis"] == "launch_prefix_caching_explicitly_disabled"
    assert frame["cache_capacity_pages"] == 99999
    assert frame["context_tokens"] != frame["cache_capacity_pages"]
    assert frame["rank_id"] == "0"
    assert frame["device_id"] == "4"
    assert frame["forward_id"] == "prefill:0"


def _usage(source: Path, *, concurrency: int, requests: int, max_running: int | None) -> None:
    (source.parent / "meta.env").write_text(
        f"INPUT_LEN=4096\nMODE=prefill\nCONCURRENCY={concurrency}\n", encoding="utf-8",
    )
    (source.parent / "cmd.sh").write_text(
        "vllm serve model --enable-prefix-caching --tensor-parallel-size 4 --max-num-seqs 32\n",
        encoding="utf-8",
    )
    summary: dict = {"concurrency": concurrency, "token_exact": True}
    if max_running is not None:
        summary["max_running"] = max_running
    (source.parent / "benchmark_summary.json").write_text(json.dumps({
        "summary": summary,
        "requests": [
            {"idx": index, "prompt_tokens": 4096, "completion_tokens": 1, "ok": True, "chunk_epochs": []}
            for index in range(requests)
        ],
    }), encoding="utf-8")


def test_one_request_on_one_device_sets_sequences_without_using_heads(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(
        _HEADER
        + _row(*_dense(3840, 3840), 10, "1")
        + _row(*_paged(256, 312190), 20, "2"),
        encoding="utf-8",
    )
    _usage(source, concurrency=1, requests=1, max_running=1)
    producer.clear_producer_caches()
    declared = producer.producer_declaration(
        source, [{"phase": "prefill", "receipt_windows": [_window("prefill:0", 3840), _window("prefill:1", 256)]}],
        phase="prefill",
    )
    frames = declared["frames"]
    assert [item["sequences_per_replica"] for item in frames] == [1, 1]
    assert {item["sequences_basis"] for item in frames} == {"one_ok_request_concurrency_one_max_running_one_single_device"}
    assert frames[0]["query_shape"][1] == 4
    assert frames[0]["sequences_per_replica"] != frames[0]["query_shape"][1]


def test_several_requests_do_not_assume_sequences_one(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(_HEADER + _row(*_dense(3840, 3840), 10, "1"), encoding="utf-8")
    _usage(source, concurrency=2, requests=2, max_running=2)
    producer.clear_producer_caches()
    declared = producer.producer_declaration(
        source, [{"phase": "prefill", "receipt_windows": [_window("prefill:0", 3840)]}], phase="prefill",
    )
    frame = declared["frames"][0]
    assert frame["schedule_role"] == "prefill_physical_step"
    assert frame["query_rows"] == 3840
    assert "sequences_per_replica" not in frame
    assert "sequences_basis" not in frame
    assert frame["query_shape"][1] == 4


def test_receipt_query_and_device_do_not_replace_the_tensor_query(tmp_path: Path):
    source = tmp_path / "kernel_details.csv"
    source.write_text(_HEADER + _row(*_dense(3840, 3840), 10, "1"), encoding="utf-8")
    declared = _prefill(source, [_window("prefill:0", 4096, device="0")], prompt=3840, cmd=None)
    frame = declared["frames"][0]
    assert frame["schedule_role"] == "model_argument_identity"
    assert frame["query_rows"] == 3840
    assert frame["context_tokens"] is None
    assert frame["forward_id"] is None
    assert "prefill_receipt_device_forward_link_absent" in declared["notes"]
