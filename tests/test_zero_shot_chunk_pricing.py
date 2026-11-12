from pathlib import Path
import json
import sys
import os
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402
from zero_shot_chunk_pricing import predict_chunk, predict_chunk_batch


def _glm():
    path = Path(os.environ.get("MINDIE_ZERO_SHOT_JSONL", ""))
    if not path.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    return next(c for c in z.load_benchmark_jsonl(path)
                if c.spec.cell_id == "glm51_dp16tp1ep16_pf_1k_c1")


def test_chunk_explicit_kv_end_changes_only_affected_work():
    spec = _glm().spec
    first = predict_chunk(spec, 512, 512)
    mid = predict_chunk(spec, 512, 2048)
    late = predict_chunk(spec, 512, 8192)
    assert first.body_ms < mid.body_ms < late.body_ms
    assert first.per_layer["gemm"] == pytest.approx(mid.per_layer["gemm"])
    assert first.per_layer["gemm"] == pytest.approx(late.per_layer["gemm"])
    assert first.per_layer["attention"] < mid.per_layer["attention"] < late.per_layer["attention"]
    assert first.per_layer["indexer"] < mid.per_layer["indexer"] < late.per_layer["indexer"]


def test_chunk_rejects_impossible_q_and_end():
    spec = _glm().spec
    with pytest.raises(ValueError, match="chunk_query_tokens_invalid"):
        predict_chunk(spec, 0, 512)
    with pytest.raises(ValueError, match="chunk_kv_end_impossible"):
        predict_chunk(spec, 1024, 512)
    with pytest.raises(ValueError, match="chunk_sequences_must_be_one"):
        predict_chunk(spec, 512, 512, sequences=2)


def test_batch_rejects_scalar_multiplier_and_mixed_ranks():
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


def test_glm_ragged_batch_conserves_tokens_and_prior_kv():
    spec = _glm().spec
    short = predict_chunk_batch(spec, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    solo = predict_chunk(spec, 512, 512)
    assert short["total_ms"] == pytest.approx(solo.prefill_body_ms)
    assert short["activated_layers"] == solo.layers
    assert short["scope"] == "single admitted batch"
    repeated = predict_chunk_batch(spec, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert repeated["total_ms"] == pytest.approx(short["total_ms"])
    assert repeated["pp_ms"] == pytest.approx(short["pp_ms"])
    same = predict_chunk_batch(spec, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
        {"ordinal": 1, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    ragged = predict_chunk_batch(spec, [
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


def test_omitted_rank_is_unspecified_and_mixed_8191_keeps_mtp_tokens():
    spec = _glm().spec
    omitted = predict_chunk_batch(spec, [
        {"ordinal": 0, "q_len": 128, "kv_end": 128, "phase": "prefill", "seq": 1},
    ])
    declared = predict_chunk_batch(spec, [
        {"ordinal": 0, "q_len": 128, "kv_end": 128, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert omitted["rank_role"] == "local_lane_unspecified"
    assert omitted["requests"][0]["rank"] is None
    assert declared["rank_role"] == "declared" and declared["requests"][0]["rank"] == 0
    assert omitted["total_ms"] == pytest.approx(declared["total_ms"])
    mixed = predict_chunk_batch(spec, [
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


def _qwen_row() -> dict:
    path = Path(os.environ.get("MINDIE_ZERO_SHOT_JSONL", ""))
    if not path.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if "smoke_qwen36_single_dc_4k_c8" not in line:
                continue
            raw = json.loads(line)
            if raw.get("cell_id") == "smoke_qwen36_single_dc_4k_c8":
                return raw
    pytest.skip("qwen36 cell absent")


def test_qwen36_declared_cobatch_is_not_a_cap_or_timing_choice():
    from zero_shot_request_prediction import _chunk_body, _prefill_spec
    from mindie_sim.prediction.piecewise.open_prefill_scheduler import (
        chunked_prefill_open_scheduler_ttft_ms,
    )
    spec = z.cell_from_dict(_qwen_row()).spec
    solo = _chunk_body(spec, 4096, 4096)
    prefill = _prefill_spec(spec, 4096)
    one = predict_chunk_batch(prefill, [
        {"ordinal": 0, "q_len": 4096, "kv_end": 4096, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert one["total_ms"] == pytest.approx(solo)
    assert one["activated_layers"] > 0
    pair = [
        {"ordinal": 0, "q_len": 4096, "kv_end": 4096, "phase": "prefill", "seq": 1, "rank": 0},
        {"ordinal": 4, "q_len": 4096, "kv_end": 4096, "phase": "prefill", "seq": 1, "rank": 0},
    ]
    # Declared budget 8192 can co-admit these two query lengths. The cap is not
    # evidence that this batch ran, and no observed latency is consulted.
    assert sum(item["q_len"] for item in pair) <= 8192
    joint = predict_chunk_batch(prefill, pair)
    assert joint["tokens"] == 8192 and joint["request_count"] == 2
    assert joint["activated_layers"] == one["activated_layers"]
    later = predict_chunk_batch(prefill, [
        {"ordinal": 0, "q_len": 4096, "kv_end": 4096, "phase": "prefill", "seq": 1, "rank": 0},
        {"ordinal": 4, "q_len": 1024, "kv_end": 8192, "phase": "prefill", "seq": 1, "rank": 0},
    ])
    assert later["tokens"] == 5120
    assert later["requests"][1]["prior_kv"] == 7168
    assert later["causal_pairs"] != joint["causal_pairs"]
    calls = []

    def body(requests):
        priced = predict_chunk_batch(prefill, requests)
        calls.append(priced)
        return priced

    wide = chunked_prefill_open_scheduler_ttft_ms(
        [4096] * 8, dp=4, max_batched_tokens=8192, max_num_seqs=32, body_batch=body)
    wide_calls = list(calls)
    calls.clear()
    split = chunked_prefill_open_scheduler_ttft_ms(
        [4096] * 8, dp=4, max_batched_tokens=4096, max_num_seqs=32, body_batch=body)
    split_calls = list(calls)
    calls.clear()
    serial = chunked_prefill_open_scheduler_ttft_ms(
        [4096] * 8, dp=4, max_batched_tokens=8192, max_num_seqs=1, body_batch=body)
    assert any(item["request_count"] == 2 and item["tokens"] == 8192 for item in wide_calls)
    assert all(item["tokens"] <= 4096 for item in split_calls)
    assert all(item["request_count"] == 1 for item in calls)
    assert wide.metadata["actual_scheduler_observed"] is False
    assert len(wide) == 8 and wide[0] != serial[0]
    assert split[0] == pytest.approx(solo)
    def _steps(priced):
        return [{"total_ms": item["total_ms"], "tokens": item["tokens"],
                 "request_count": item["request_count"], "causal_pairs": item["causal_pairs"],
                 "pp_ms": item["pp_ms"], "collective_ms": item["collective_ms"],
                 "activated_layers": item["activated_layers"]} for item in priced]

    historical = 500.75074351458574
    report = {
        "solo_q4096_ms": solo,
        "one_request_batch_ms": one["total_ms"],
        "historical_solo_q4096_ms": historical,
        "solo_minus_historical": solo - historical,
        "joint_q4096x2_ms": joint["total_ms"],
        "joint_causal_pairs": joint["causal_pairs"],
        "joint_pp_ms": joint["pp_ms"],
        "joint_collective_ms": joint["collective_ms"],
        "one_causal_pairs": one["causal_pairs"],
        "one_pp_ms": one["pp_ms"],
        "one_collective_ms": one["collective_ms"],
        "later_tokens": later["tokens"],
        "later_causal_pairs": later["causal_pairs"],
        "later_prior_kv": later["requests"][1]["prior_kv"],
        "later_total_ms": later["total_ms"],
        "activated_layers": joint["activated_layers"],
        "wide_ordinal0_ms": wide[0],
        "split_ordinal0_ms": split[0],
        "serial_ordinal0_ms": serial[0],
        "wide_steps": len(wide.steps),
        "split_steps": len(split.steps),
        "serial_steps": len(serial.steps),
        "wide_priced_steps": _steps(wide_calls),
        "split_priced_steps": _steps(split_calls),
        "serial_priced_steps": _steps(calls),
    }
    Path(os.environ.get("KB_PRICE_REPORT", "/tmp/mindie-7337-20261111-1457/kb-price.json")).write_text(
        json.dumps(report), encoding="utf-8")
