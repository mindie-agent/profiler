"""Self-contained chunk-pricing and co-batch open-scheduler tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402
from zero_shot_chunk_pricing import predict_chunk, predict_chunk_batch  # noqa: E402


@pytest.fixture(scope="module")
def glm_spec(tmp_path_factory: pytest.TempPathFactory):
    src = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm51_mxfp4_dp16tp1ep16_pf1k.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    doc["model"]["layers"] = 4
    if "layer_plans" in doc["model"]:
        doc["model"]["layer_plans"] = list(doc["model"]["layer_plans"])[:4]
    compact = tmp_path_factory.mktemp("chunk_cases") / "compact_glm51.json"
    compact.write_text(json.dumps(doc), encoding="utf-8")
    return z.CellSpec(
        "glm51_compact_pf", "unit", "prefill", compact,
        "GLM-5.1/W4A4C8", 1024, 1, 1, 1, 16, 16, 1,
    )


@pytest.fixture(scope="module")
def qwen36_spec(tmp_path_factory: pytest.TempPathFactory):
    src = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen36_highconc_c4.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    doc["model"]["layers"] = 4
    if "layer_plans" in doc["model"]:
        doc["model"]["layer_plans"] = list(doc["model"]["layer_plans"])[:4]
    compact = tmp_path_factory.mktemp("chunk_qwen36") / "compact_qwen36.json"
    compact.write_text(json.dumps(doc), encoding="utf-8")
    return z.CellSpec(
        "smoke_qwen36_single_dc_4k_c8", "unit", "decode", compact,
        "Qwen3.6-27B", 512, 8, 4, 2, 4, 1, 1,
    )


def test_chunk_explicit_kv_end_changes_only_affected_work(glm_spec) -> None:
    first = predict_chunk(glm_spec, 512, 512)
    mid = predict_chunk(glm_spec, 512, 2048)
    late = predict_chunk(glm_spec, 512, 8192)
    assert first.body_ms < mid.body_ms < late.body_ms
    assert first.per_layer["gemm"] == pytest.approx(mid.per_layer["gemm"])
    assert first.per_layer["gemm"] == pytest.approx(late.per_layer["gemm"])
    assert first.per_layer["attention"] < mid.per_layer["attention"] < late.per_layer["attention"]
    assert first.per_layer["indexer"] < mid.per_layer["indexer"] < late.per_layer["indexer"]


def test_chunk_rejects_impossible_q_and_end(glm_spec) -> None:
    with pytest.raises(ValueError, match="chunk_query_tokens_invalid"):
        predict_chunk(glm_spec, 0, 512)
    with pytest.raises(ValueError, match="chunk_kv_end_impossible"):
        predict_chunk(glm_spec, 1024, 512)
    with pytest.raises(ValueError, match="chunk_sequences_must_be_one"):
        predict_chunk(glm_spec, 512, 512, sequences=2)


def test_batch_rejects_scalar_multiplier_and_mixed_ranks() -> None:
    spec = z.CellSpec("batch-guard", "out", "prefill", None, "guard", 4, 1, 1, 1, 1, 1, 1)
    with pytest.raises(ValueError, match="chunk_batch_sequences_must_be_one"):
        predict_chunk_batch(spec, [{"q_len": 4, "kv_end": 4, "phase": "prefill"}], sequences=2)
    with pytest.raises(ValueError, match="chunk_batch_rank_not_single_lane"):
        predict_chunk_batch(spec, [
            {"ordinal": 0, "q_len": 4, "kv_end": 4, "phase": "prefill", "seq": 1, "rank": 0},
            {"ordinal": 1, "q_len": 4, "kv_end": 4, "phase": "prefill", "seq": 1, "rank": 1},
        ])
    with pytest.raises(ValueError, match="chunk_batch_rank_partial"):
        predict_chunk_batch(spec, [
            {"ordinal": 0, "q_len": 4, "kv_end": 4, "phase": "prefill", "rank": 0},
            {"ordinal": 1, "q_len": 4, "kv_end": 4, "phase": "prefill"},
        ])
    with pytest.raises(ValueError, match="chunk_batch_physical_tokens_partial"):
        predict_chunk_batch(spec, [
            {"ordinal": 0, "q_len": 4, "kv_end": 4, "phase": "prefill", "physical_tokens": 4},
            {"ordinal": 1, "q_len": 1, "kv_end": 1, "phase": "decode"},
        ])


def test_glm_ragged_batch_conserves_tokens_and_prior_kv(glm_spec) -> None:
    short = predict_chunk_batch(glm_spec, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    solo = predict_chunk(glm_spec, 512, 512)
    assert short["total_ms"] == pytest.approx(solo.prefill_body_ms)
    assert short["activated_layers"] == solo.layers == 4
    assert short["scope"] == "single admitted batch"
    repeated = predict_chunk_batch(glm_spec, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert repeated["total_ms"] == pytest.approx(short["total_ms"])
    assert repeated["pp_ms"] == pytest.approx(short["pp_ms"])
    same = predict_chunk_batch(glm_spec, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
        {"ordinal": 1, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    ragged = predict_chunk_batch(glm_spec, [
        {"ordinal": 0, "q_len": 128, "kv_end": 128, "phase": "prefill", "seq": 1, "rank": 0},
        {"ordinal": 1, "q_len": 512, "kv_end": 2048, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert same["request_count"] == 2 and same["tokens"] == 1024
    assert same["activated_layers"] == short["activated_layers"]
    assert same["causal_pairs"] == 2 * short["causal_pairs"]
    assert ragged["tokens"] == 640
    assert ragged["requests"][1]["prior_kv"] == 1536
    assert ragged["causal_pairs"] != same["causal_pairs"]
    assert ragged["per_layer"]["attention"] > same["per_layer"]["attention"]
    assert sum(ragged["per_request_ms"].values()) == pytest.approx(ragged["total_ms"])
    assert ragged["total_ms"] != pytest.approx(short["total_ms"] * 32)


def test_omitted_rank_is_unspecified_and_mixed_8191_keeps_mtp_tokens(glm_spec) -> None:
    omitted = predict_chunk_batch(glm_spec, [
        {"ordinal": 0, "q_len": 128, "kv_end": 128, "phase": "prefill", "seq": 1},
    ])
    declared = predict_chunk_batch(glm_spec, [
        {"ordinal": 0, "q_len": 128, "kv_end": 128, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert omitted["rank_role"] == "local_lane_unspecified"
    assert omitted["requests"][0]["rank"] is None
    assert declared["rank_role"] == "declared" and declared["requests"][0]["rank"] == 0
    assert omitted["total_ms"] == pytest.approx(declared["total_ms"])
    mixed = predict_chunk_batch(glm_spec, [
        {"ordinal": 0, "q_len": 1, "kv_end": 8192, "phase": "decode", "seq": 1,
         "draft_len": 2, "query_ranges": [[0, 1]], "physical_tokens": 1},
        {"ordinal": 4, "q_len": 8191, "kv_end": 8191, "phase": "prefill", "seq": 1,
         "draft_len": 1, "physical_tokens": 8191},
    ])
    assert mixed["tokens"] == 8192 and mixed["request_count"] == 2
    assert mixed["physical_tokens"] == 8192
    assert mixed["activated_layers"] == omitted["activated_layers"]
    assert mixed["rank_role"] == "local_lane_unspecified"
    assert mixed["requests"][0]["rank"] is None
    assert mixed["requests"][0]["phase"] == "decode"
    assert mixed["requests"][0]["draft_len"] == 2
    assert mixed["requests"][0]["query_ranges"] == [[0, 1]]
    assert mixed["requests"][0]["prior_kv"] == 8191
    assert mixed["requests"][1]["q_len"] == 8191 and mixed["requests"][1]["prior_kv"] == 0
    assert sum(mixed["per_request_ms"].values()) == pytest.approx(mixed["total_ms"])


def test_qwen36_declared_cobatch_is_not_a_cap_or_timing_choice(qwen36_spec) -> None:
    from zero_shot_request_prediction import _chunk_body, _prefill_spec
    from mindie_sim.prediction.piecewise.open_prefill_scheduler import (
        chunked_prefill_open_scheduler_ttft_ms,
    )
    solo = _chunk_body(qwen36_spec, 512, 512)
    prefill = _prefill_spec(qwen36_spec, 512)
    one = predict_chunk_batch(prefill, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert one["total_ms"] == pytest.approx(solo)
    assert one["activated_layers"] == 4
    pair = [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
        {"ordinal": 4, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ]
    assert sum(item["q_len"] for item in pair) <= 1024
    joint = predict_chunk_batch(prefill, pair)
    assert joint["tokens"] == 1024 and joint["request_count"] == 2
    assert joint["activated_layers"] == one["activated_layers"]
    later = predict_chunk_batch(prefill, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
        {"ordinal": 4, "q_len": 256, "kv_end": 1024, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert later["tokens"] == 768
    assert later["requests"][1]["prior_kv"] == 768
    assert later["causal_pairs"] != joint["causal_pairs"]
    calls = []
    batch_memo = {}

    def body(requests):
        sig = tuple((r["q_len"], r["kv_end"], r["phase"]) for r in requests)
        if sig not in batch_memo:
            batch_memo[sig] = predict_chunk_batch(prefill, requests)
        priced = batch_memo[sig]
        calls.append(priced)
        return priced

    wide = chunked_prefill_open_scheduler_ttft_ms(
        [512] * 8, dp=4, max_batched_tokens=1024, max_num_seqs=32, body_batch=body)
    wide_calls = list(calls)
    calls.clear()
    split = chunked_prefill_open_scheduler_ttft_ms(
        [512] * 8, dp=4, max_batched_tokens=512, max_num_seqs=32, body_batch=body)
    split_calls = list(calls)
    calls.clear()
    serial = chunked_prefill_open_scheduler_ttft_ms(
        [512] * 8, dp=4, max_batched_tokens=1024, max_num_seqs=1, body_batch=body)
    assert any(item["request_count"] == 2 and item["tokens"] == 1024 for item in wide_calls)
    assert all(item["tokens"] <= 512 for item in split_calls)
    assert all(item["request_count"] == 1 for item in calls)
    assert wide.metadata["actual_scheduler_observed"] is False
    assert len(wide) == 8 and wide[0] != serial[0]
    assert split[0] == pytest.approx(solo)
