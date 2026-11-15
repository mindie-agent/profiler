"""Focused tests for original client-request acquisition and unit/boundary semantics.

[Role] Exercise the producer JSON fields, TTFT-sorted stream order versus
  launch-order first-token list, explicit request ordinals, units, aggregate
  separation, and missing/conflict states without touching the native reader.

[Invariants] Raw seconds/counts are preserved; no request id is invented;
  ambiguous TTFT duplicates stay ambiguous; cell aggregates are never request
  L4 values; missing/conflict cells stay in the denominator.

[Timeouts & Locks] Tiny tmp_path JSON/CMD fixtures; no network, model or device.

[Side-Effect Policy] All generated artifacts live under pytest tmp_path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))

import zero_shot_client_requests as client  # noqa: E402
import zero_shot_client_source as source  # noqa: E402


def _record(cell_id: str, *, concurrency: int = 1, streams=None,
            first=None, mode: str = "profile_prefill") -> dict:
    streams = streams if streams is not None else [{
        "ok": True, "ttft_s": 1.5, "e2e_s": 1.6, "completion_tokens": 1,
        "chunks": 1, "itl_mean_s": None, "itl_p50_s": None}]
    first = first if first is not None else [1.5000002] * concurrency
    return {
        "tag": cell_id, "bases": ["http://127.0.0.1:18410"], "mode": mode,
        "prompt_tokens": 16, "shared_tokens": 8, "fresh_tokens": 8,
        "max_tokens": 1 if mode == "profile_prefill" else 4,
        "concurrency": concurrency, "warmup_requests": 1,
        "warmup_max_tokens": 2, "warmup_prompt_tokens": 8,
        "started": "2026-11-07T03:40:46Z", "warmup": [], "warmup_ok": 1,
        "start_profile": [200], "start_profile_s": 0.125, "stop_profile": [200],
        "measure_window_s": 2.5, "streams": streams, "failed_streams": [],
        "success": len(streams), "failed": 0, "first_token_latencies_s": first,
        "ttft_mean_s": 1.5, "ttft_p50_s": 1.5, "tpot_mean_s": 0.1,
        "tpot_p50_s": 0.1, "window_s": 0.1, "out_tokens_total": 1,
        "out_tokens_per_s": 10.0,
    }


def _layout(tmp_path: Path, cell_id: str, record: dict) -> tuple[Path, dict]:
    case = "case_x"
    suffix = cell_id[len(case) + 1:]
    root = tmp_path / "root"
    measured = root / "out" / case / "measured"
    measured.mkdir(parents=True)
    (measured / f"{cell_id}.json").write_text(json.dumps(record), encoding="utf-8")
    cell_dir = root / "out" / case / suffix
    cell_dir.mkdir(parents=True)
    (cell_dir / "cmd.sh").write_text(
        f"python3 bench_cell.py --mode {record['mode']} "
        f"--prompt-tokens {record['prompt_tokens']} "
        f"--shared-tokens {record['shared_tokens']} "
        f"--max-tokens {record['max_tokens']} "
        f"--concurrency {record['concurrency']} "
        f"--warmup {record['warmup_requests']} --tag {cell_id}\n",
        encoding="utf-8")
    (root / "cases").mkdir()
    (root / "cases" / f"{case}.json").write_text(json.dumps({
        "max_num_batched_tokens": 8192, "max_num_seqs": 128,
        "nodes": ["host-a"], "dp": 1, "tp": 1}), encoding="utf-8")
    (root / "out" / case / "status.json").write_text(json.dumps({
        "cells": [{"tag": cell_id, "name": suffix, "captured": True,
                   "started": "2026-11-07T03:40:40Z",
                   "finished": "2026-11-07T03:41:10Z"}]}), encoding="utf-8")
    row_phase = "prefill" if record["mode"] == "profile_prefill" else "decode"
    row = {"cell_id": cell_id, "phase": row_phase, "model_case": "unused"}
    return root, row


def test_c1_prefill_units_boundaries_ordinal_and_aggregate_separation(tmp_path):
    cell_id = "case_x_pf_1k_c1"
    record = _record(cell_id)
    root, row = _layout(tmp_path, cell_id, record)
    capture = client.client_capture(row, roots=[root])
    assert capture.status == "acquired" and capture.conflicts == ()
    assert capture.measured_sha256 and len(capture.measured_sha256) == 64
    assert capture.original_row_sha256 and capture.original_row_sha_basis == "canonical_json"
    assert capture.units["ttft_s"] == "seconds"
    assert capture.units["completion_tokens"] == "tokens"
    assert "client send" in capture.boundaries["ttft_s"]
    assert capture.first_token_latencies_s == (1.5000002,)
    request = capture.requests[0]
    assert request.launch_ordinal == 0
    assert request.stream_join_status == "exact_unique_rounded_ttft"
    assert request.stream_rank == 0 and request.raw_ttft_s == 1.5000002
    assert request.ttft_s == 1.5 and request.ttft_ms == 1500.0
    assert request.e2e_s == 1.6 and request.itl_mean_s is None
    assert request.request_seed == 1234 and request.prompt_seed == 1025
    assert "ordinal=0" in request.key and "ctx=2026-11-07T03:40:46Z" in request.key
    assert capture.mode_boundary == "profile_single_phase"
    assert capture.producer["rack"] == "unknown"
    # Aggregate is separate and not substituted for the request value.
    assert capture.cell_aggregate["ttft_mean_s"] == 1.5
    assert capture.measure_window_s == 2.5  # cell lifecycle, not request L4
    assert capture.launch_declaration["cmd_args"]["concurrency"] == "1"
    assert capture.launch_declaration["server_chunk_budget"] == 8192
    assert capture.launch_declaration["seed_basis"] == "producer_default_1024"
    assert capture.status_cell["captured"] is True


def test_c_gt1_stream_order_is_ttft_rank_and_launch_ordinal_is_exact(tmp_path):
    cell_id = "case_x_dc_1k_c2"
    # Producer writes streams sorted by ttft_s; launch order lives in first_token_latencies_s.
    streams = [
        {"ok": True, "ttft_s": 1.0, "e2e_s": 2.0, "completion_tokens": 2,
         "chunks": 2, "itl_mean_s": 0.4, "itl_p50_s": 0.4},
        {"ok": True, "ttft_s": 2.0, "e2e_s": 3.0, "completion_tokens": 2,
         "chunks": 2, "itl_mean_s": 0.5, "itl_p50_s": 0.5},
    ]
    record = _record(cell_id, concurrency=2, streams=streams,
                     first=[1.0000001, 2.0000002], mode="profile_decode")
    record["max_tokens"] = 4
    root, row = _layout(tmp_path, cell_id, record)
    capture = client.client_capture(row, roots=[root])
    assert [item.ttft_s for item in capture.requests] == [1.0, 2.0]
    assert [item.stream_rank for item in capture.requests] == [0, 1]
    assert [item.launch_ordinal for item in capture.requests] == [0, 1]
    assert [item.request_seed for item in capture.requests] == [1234, 1235]
    assert capture.request_id_status == "ordinal_ttft_keyed"
    assert capture.full_join_count == 2 and capture.ambiguous_join_count == 0


def test_ambiguous_ttft_duplicate_keeps_ordinal_unresolved(tmp_path):
    cell_id = "case_x_dc_1k_c2"
    streams = [
        {"ok": True, "ttft_s": 1.0, "e2e_s": 2.0, "completion_tokens": 2,
         "chunks": 2, "itl_mean_s": 0.4, "itl_p50_s": 0.4},
        {"ok": True, "ttft_s": 1.0, "e2e_s": 2.1, "completion_tokens": 2,
         "chunks": 2, "itl_mean_s": 0.5, "itl_p50_s": 0.5},
    ]
    record = _record(cell_id, concurrency=2, streams=streams,
                     first=[1.0, 1.0], mode="profile_decode")
    root, row = _layout(tmp_path, cell_id, record)
    capture = client.client_capture(row, roots=[root])
    assert [item.launch_ordinal for item in capture.requests] == [0, 1]
    assert all(item.stream_join_status == "ambiguous_duplicate_rounded_ttft"
               for item in capture.requests)
    assert all(item.stream_rank is None and item.observed_stream is None
               for item in capture.requests)
    assert all(item.candidate_stream_ranks == (0, 1) for item in capture.requests)
    assert [item.request_seed for item in capture.requests] == [1234, 1235]
    assert [item.prompt_seed for item in capture.requests] == [1025, 1026]
    assert "observed_stream_metadata_ambiguous" in capture.out_of_domain
    assert all("ordinal=" in item.key for item in capture.requests)
    assert all(stream.join_status == "ambiguous_rounded_ttft"
               and stream.candidate_ordinals == (0, 1) for stream in capture.streams)


def test_conflict_missing_and_exact_line_sha_states(tmp_path):
    cell_id = "case_x_pf_1k_c1"
    record = _record(cell_id)
    record["concurrency"] = 2  # mismatch vs one stream
    root, row = _layout(tmp_path, cell_id, record)
    capture = client.client_capture(row, roots=[root])
    assert capture.status == "conflict"
    assert "concurrency_stream_count_mismatch" in capture.conflicts
    missing = client.client_capture({"cell_id": "case_x_missing", "phase": "decode"},
                                    roots=[root])
    assert missing.status == "missing" and missing.reason == "measured_client_json_absent"
    assert missing.requests == () and missing.out_of_domain == ("missing_source",)
    # Exact original line SHA.
    line = json.dumps(row, sort_keys=True)
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text(line + "\n", encoding="utf-8")
    (parsed, sha), = list(client.iter_original_rows_with_sha(rows_path))
    assert parsed["cell_id"] == cell_id
    capture = client.client_capture(parsed, roots=[root], row_sha256=sha)
    assert capture.original_row_sha256 == sha
    assert capture.original_row_sha_basis == "exact_line_with_newline"


def test_summary_counts_94_separately_and_keeps_637(tmp_path):
    records = []
    rows = []
    for index, (phase, conc) in enumerate((("prefill", 1), ("decode", 1), ("decode", 2))):
        cell_id = f"case_x_c{index}"
        mode = "profile_prefill" if phase == "prefill" else "profile_decode"
        streams = [{"ok": True, "ttft_s": 1.0 + index + i,
                    "e2e_s": 2.0 + index + i, "completion_tokens": 2,
                    "chunks": 2, "itl_mean_s": 0.1, "itl_p50_s": 0.1}
                   for i in range(conc)]
        record = _record(cell_id, concurrency=conc, streams=streams,
                         first=[1.0 + index + i for i in range(conc)], mode=mode)
        records.append((cell_id, record))
        rows.append({"cell_id": cell_id, "phase": phase})
    root = tmp_path / "root"
    measured = root / "out" / "case_x" / "measured"
    measured.mkdir(parents=True)
    for cell_id, record in records:
        (measured / f"{cell_id}.json").write_text(json.dumps(record), encoding="utf-8")
    summary = client.summarize_client_requests(rows, roots=[root])
    assert summary["cells"] == 3
    assert summary["requests"] == 4
    assert summary["c1_cells"] == 2
    assert summary["c_gt1_cells"] == 1
    assert summary["singleton_94_cells"] == 1
    assert summary["other_637_cells"] == 2
    assert summary["cell_status"]["acquired"] == 3
    assert summary["cell_status"]["missing"] == 0
    assert summary["cell_status"]["conflict"] == 0


def test_mixed_tail_geometry_is_actual_and_p7_has_no_target_leak(tmp_path):
    cell_id = "case_x_pd_1k_c4"
    streams = [{"ok": True, "ttft_s": 1.0 + i, "e2e_s": 2.0 + i,
                "completion_tokens": 2, "chunks": 2,
                "itl_mean_s": 0.1, "itl_p50_s": 0.1} for i in range(4)]
    record = _record(cell_id, concurrency=4, streams=streams,
                     first=[1.0, 2.0, 3.0, 4.0], mode="profile_pd")
    record["prompt_tokens"] = 16
    record["shared_tokens"] = 8
    record["fresh_tokens"] = 8
    record["mix_count"] = 2
    record["mix_prompt_tokens"] = 8
    record["max_tokens"] = 4
    root, row = _layout(tmp_path, cell_id, record)
    declarations = list(client.iter_prediction_declarations([row], roots=[root]))
    assert len(declarations) == 4
    assert [item["ordinal"] for item in declarations] == [0, 1, 2, 3]
    assert declarations[0]["prompt_tokens"] == 16
    assert declarations[0]["shared_tokens"] == 8
    assert declarations[0]["mix_class"] == "base"
    assert declarations[0]["prompt_seed"] == 1025
    assert declarations[2]["prompt_tokens"] == 8
    assert declarations[2]["shared_tokens"] == 0
    assert declarations[2]["fresh_tokens"] == 8
    assert declarations[2]["mix_class"] == "mixed_tail"
    assert declarations[2]["mix_index"] == 0
    assert declarations[2]["prompt_seed"] == 8025
    assert declarations[3]["prompt_seed"] == 8026
    assert declarations[2]["request_seed"] == 1236
    assert not ({"ttft_s", "e2e_s", "itl_mean_s", "observed_stream"} &
                set(declarations[2]))


def test_original_override_conflict_preserves_measured_cell_and_requests(tmp_path):
    cell_id = "case_x_dc_1k_c2"
    streams = [{"ok": True, "ttft_s": 1.0 + i, "e2e_s": 2.0 + i,
                "completion_tokens": 2, "chunks": 2,
                "itl_mean_s": 0.1, "itl_p50_s": 0.1} for i in range(2)]
    record = _record(cell_id, concurrency=2, streams=streams,
                     first=[1.0, 2.0], mode="profile_decode")
    record["max_tokens"] = 4
    root, row = _layout(tmp_path, cell_id, record)
    clean = client.client_capture(row, roots=[root])
    assert clean.status == "acquired" and clean.source_conflicts == ()
    tampered = dict(row, concurrency=9, prompt_tokens=1,
                    max_tokens=1, phase="prefill")
    capture = client.client_capture(tampered, roots=[root])
    assert capture.status == "source_conflict"
    assert len(capture.requests) == 2
    assert [item.ttft_s for item in capture.requests] == [1.0, 2.0]
    assert {(item["field"], item["supplied"]) for item in capture.source_conflicts} == {
        ("phase", "prefill"), ("concurrency", 9), ("prompt_tokens", 1),
        ("max_tokens", 1)}
    assert "row_override_source_conflict" in capture.out_of_domain
    # Optional blank/absent fields are not mandatory receipts.
    partial = {"cell_id": cell_id, "phase": "decode"}
    assert client.client_capture(partial, roots=[root]).status == "acquired"


def test_declarations_survive_missing_outcomes_and_unknown_geometry(tmp_path):
    cell_id = "case_x_pd_1k_c4"
    streams = [{"ok": True, "ttft_s": 1.0 + i, "e2e_s": 2.0 + i,
                "completion_tokens": 2, "chunks": 2,
                "itl_mean_s": 0.1, "itl_p50_s": 0.1} for i in range(4)]
    record = _record(cell_id, concurrency=4, streams=streams,
                     first=[1.0, 2.0, 3.0, 4.0], mode="profile_pd")
    record["mix_count"] = 2
    record["mix_prompt_tokens"] = 8
    record["prompt_tokens"] = 16
    record["shared_tokens"] = 8
    record["max_tokens"] = 4
    root, row = _layout(tmp_path, cell_id, record)
    clean = list(client.iter_prediction_declarations([row], roots=[root]))
    assert len(clean) == 4
    measured = root / "out" / "case_x" / "measured" / f"{cell_id}.json"
    no_first = dict(record)
    no_first.pop("first_token_latencies_s", None)
    measured.write_text(json.dumps(no_first), encoding="utf-8")
    assert list(client.iter_prediction_declarations([row], roots=[root])) == clean
    no_first_capture = client.client_capture(row, roots=[root])
    assert no_first_capture.orphan_stream_ranks == (0, 1, 2, 3)
    assert no_first_capture.outcome_status == "ttft_missing"
    assert client.p6_interface(no_first_capture)["cell"]["orphan_stream_ranks"] == [0, 1, 2, 3]
    no_streams = dict(no_first)
    no_streams.pop("streams", None)
    measured.write_text(json.dumps(no_streams), encoding="utf-8")
    assert list(client.iter_prediction_declarations([row], roots=[root])) == clean
    capture = client.client_capture(row, roots=[root])
    assert capture.declared_count == 4
    assert len(capture.requests) == 0
    assert capture.missing_ordinals == (0, 1, 2, 3)
    assert capture.outcome_status == "missing"
    interface = client.p6_interface(capture)
    assert interface["cell"]["declared_count"] == 4
    assert interface["cell"]["observed_count"] == 0
    assert interface["cell"]["missing_ordinals"] == [0, 1, 2, 3]

    # Truly missing cmd/measured concurrency and prompt: unknown, never fabricated.
    unknown_id = "case_x_unknown"
    unknown = {
        "tag": unknown_id, "mode": "profile_decode",
        "bases": ["http://127.0.0.1:1"], "started": "2026-11-07T00:00:00Z",
        "streams": [], "success": 0, "failed": 0,
    }
    (root / "out" / "case_x" / "measured" / f"{unknown_id}.json").write_text(
        json.dumps(unknown), encoding="utf-8")
    source._measured_index.cache_clear()
    declared = list(client.iter_prediction_declarations(
        [{"cell_id": unknown_id, "phase": "decode"}], roots=[root]))
    assert declared == []
    unknown_capture = client.client_capture(
        {"cell_id": unknown_id, "phase": "decode"}, roots=[root])
    assert unknown_capture.declared_count is None
    assert unknown_capture.declaration_status == "declaration_unknown_missing_concurrency"
    assert unknown_capture.status == "declaration_unknown"
