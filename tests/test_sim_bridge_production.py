"""C16: production export-sim-case must not synthesize request/scheduler facts."""
from __future__ import annotations

import json
from copy import deepcopy

import pytest

from mindie_profiler import sim_bridge
from mindie_profiler.events import ProfilerUsageError


def _complete_source():
    return {
        "npu_type": "A3",
        "model_name": "custom-inline",
        "model_config": {
            "hidden_size": 1024,
            "num_attention_heads": 8,
            "num_hidden_layers": 2,
            "intermediate_size": 3072,
            "vocab_size": 1024,
        },
        "workload": {
            "batch_size": 2, "seq_len": 128, "decode_steps": 8,
            "phase": "decode",
        },
        "runtime": {
            "max_num_seqs": 2,
            "max_num_batched_tokens": 256,
            "max_model_len": 1024,
            "kv_block_size": 128,
            "enable_chunked_prefill": False,
        },
    }


def test_missing_facts_raise_concrete_gaps_and_write_no_case(tmp_path):
    output = tmp_path / "case.json"
    with pytest.raises(ProfilerUsageError, match=r"sim_case_incomplete:") as caught:
        sim_bridge.export_sim_case({}, output=output)
    assert not output.exists()
    gaps = set(caught.value.gaps)
    assert {"workload.batch_size", "workload.seq_len", "workload.decode_steps",
            "runtime.max_num_seqs", "runtime.max_num_batched_tokens",
            "runtime.max_model_len", "runtime.kv_block_size",
            "runtime.enable_chunked_prefill", "model.missing"} <= gaps

    with pytest.raises(ProfilerUsageError) as model_known:
        sim_bridge.export_sim_case({}, model="qwen3.6-27b")
    assert "model.missing" not in set(model_known.value.gaps)
    assert "runtime.max_num_seqs" in set(model_known.value.gaps)


def test_diagnostic_mode_lists_filled_defaults_and_is_not_production(tmp_path):
    output = tmp_path / "diagnostic.json"
    case = sim_bridge.export_sim_case({}, output=output, diagnostic=True)
    metadata = case["runtime"]["metadata"]
    assert metadata["production_prediction"] is False
    assert metadata["diagnostic_mode"] is True
    assert "runtime.max_num_seqs" in metadata["diagnostic_gaps"]
    assert metadata["diagnostic_filled_values"]["runtime.max_num_seqs"] == 16
    assert metadata["diagnostic_filled_values"]["runtime.max_model_len"] == 32768
    assert metadata["diagnostic_filled_values"]["runtime.enable_chunked_prefill"] is True
    assert metadata["diagnostic_filled_values"]["workload.batch_size"] == 1
    assert json.loads(output.read_text()) == case


def test_complete_request_facts_export_production_values():
    case = sim_bridge.export_sim_case(_complete_source())
    assert case["model"]["hidden_size"] == 1024
    assert case["model"]["layers"] == 2
    assert case["runtime"]["max_num_seqs"] == 2
    assert case["runtime"]["max_model_len"] == 1024
    assert case["runtime"]["enable_chunked_prefill"] is False
    assert case["runtime"]["metadata"].get("production_prediction") is None
    assert "diagnostic_gaps" not in case["runtime"]["metadata"]


def test_complete_case_roundtrip_is_byte_equivalent():
    source = sim_bridge.export_sim_case(_complete_source())
    again = sim_bridge.export_sim_case(deepcopy(source))
    assert again == source
    assert json.dumps(again, sort_keys=True) == json.dumps(source, sort_keys=True)


def test_complete_raw_source_with_explicit_override_rebuilds():
    changed = sim_bridge.export_sim_case(
        _complete_source(), seq_len=64, batch_size=1)
    assert changed["workload"]["requests"][0]["prompt_tokens"] == 64
    assert len(changed["workload"]["requests"]) == 1


def test_native_path_remains_available_when_model_case_is_missing():
    observations = sim_bridge.export_native_observations(
        "tests/fixtures/r64_qbmm_dual_load/kernel_details.csv",
        hardware="Ascend950DT_9582", phase="prefill",
    )
    requests = sim_bridge.native_prediction_requests(observations)
    bridge = sim_bridge.predict_native_requests(
        requests, hardware="Ascend950DT_9582", phase="prefill")
    assert bridge["counts"]["requests"] == 2
    assert bridge["counts"]["status_modeled"] == 2
    assert all(row["status"] == "modeled" and row["duration_ms"] > 0
               for row in bridge["predictions"])


def test_cli_production_gap_exits_2_and_diagnostic_exits_0(tmp_path):
    source = tmp_path / "empty.json"
    source.write_text("{}", encoding="utf-8")
    output = tmp_path / "out.json"
    assert sim_bridge.main([
        "export-sim-case", "--input", str(source), "--output", str(output),
    ]) == 2
    assert not output.exists()
    assert sim_bridge.main([
        "export-sim-case", "--input", str(source), "--output", str(output),
        "--diagnostic",
    ]) == 0
    case = json.loads(output.read_text())
    assert case["runtime"]["metadata"]["production_prediction"] is False


def test_heterogeneous_requests_keep_geometry_and_arrivals():
    source = _complete_source()
    source["workload"] = {"phase": "decode"}
    source["client_cell"] = {"per_request": [
        {"request_id": "a", "arrival_ms": 0, "prompt_tokens": 128,
         "requested_max_tokens": 1},
        {"request_id": "b", "arrival_ms": 10, "prompt_tokens": 256,
         "requested_max_tokens": 8},
    ]}
    case = sim_bridge.export_sim_case(source)
    requests = case["workload"]["requests"]
    assert [(row["request_id"], row["arrival_ms"], row["prompt_tokens"],
             row["output_tokens"]) for row in requests] == [
        ("a", 0.0, 128, 1), ("b", 10.0, 256, 8)]
    assert sum(row["prompt_tokens"] for row in requests) == 384
    assert sum(row["output_tokens"] for row in requests) == 9


def test_complete_case_missing_request_fact_is_not_certified():
    source = _complete_source()
    source["client_cell"] = {"per_request": [
        {"request_id": "a", "arrival_ms": 0, "prompt_tokens": 128,
         "requested_max_tokens": 1},
        {"request_id": "b", "arrival_ms": 10, "prompt_tokens": 256,
         "requested_max_tokens": 8},
    ]}
    case = sim_bridge.export_sim_case(source)
    del case["workload"]["requests"][1]["prompt_tokens"]
    with pytest.raises(ProfilerUsageError, match=r"sim_case_incomplete:") as caught:
        sim_bridge.export_sim_case(case)
    assert "workload.requests[1].prompt_tokens" in caught.value.gaps


def test_complete_homogeneous_case_override_applies_before_construction():
    source = sim_bridge.export_sim_case(_complete_source())
    assert len(source["workload"]["requests"]) == 2
    changed = sim_bridge.export_sim_case(source, seq_len=64, batch_size=1)
    requests = changed["workload"]["requests"]
    assert len(requests) == 1
    assert requests[0]["request_id"] == "req-0"
    assert requests[0]["arrival_ms"] == 0.0
    assert requests[0]["prompt_tokens"] == 64
    assert requests[0]["output_tokens"] == 8


def test_heterogeneous_seq_override_keeps_arrivals_and_outputs():
    source = _complete_source()
    source["workload"] = {"phase": "decode"}
    source["client_cell"] = {"per_request": [
        {"request_id": "a", "arrival_ms": 0, "prompt_tokens": 128,
         "requested_max_tokens": 1},
        {"request_id": "b", "arrival_ms": 10, "prompt_tokens": 256,
         "requested_max_tokens": 8},
    ]}
    case = sim_bridge.export_sim_case(source, seq_len=64)
    requests = case["workload"]["requests"]
    assert [(row["request_id"], row["arrival_ms"], row["prompt_tokens"],
             row["output_tokens"]) for row in requests] == [
        ("a", 0.0, 64, 1), ("b", 10.0, 64, 8)]
    assert sum(row["prompt_tokens"] for row in requests) == 128
    assert sum(row["output_tokens"] for row in requests) == 9


def test_aggregate_output_average_is_not_a_production_request_fact():
    source = _complete_source()
    source["workload"] = {"batch_size": 2, "seq_len": 128, "phase": "decode"}
    source["benchmark_summary"] = {"summary": {"out_tokens": 9, "n_ok": 2}}
    with pytest.raises(ProfilerUsageError) as caught:
        sim_bridge.export_sim_case(source)
    assert "workload.decode_steps.aggregate_only" in caught.value.gaps

    diagnostic = sim_bridge.export_sim_case(source, diagnostic=True)
    aggregate = diagnostic["runtime"]["metadata"]["diagnostic_aggregate"]
    assert aggregate["out_tokens"] == 9
    assert aggregate["n_ok"] == 2
    assert aggregate["per_request_output"] == 4


def test_explicit_homogeneous_two_output4_is_legal():
    source = _complete_source()
    source["workload"] = {"batch_size": 2, "seq_len": 128,
                          "decode_steps": 4, "phase": "decode"}
    case = sim_bridge.export_sim_case(source)
    assert len(case["workload"]["requests"]) == 2
    assert [row["output_tokens"] for row in case["workload"]["requests"]] == [4, 4]


def test_aggregate_summary_cli_rejects_without_writing(tmp_path):
    source = _complete_source()
    source["workload"] = {"batch_size": 2, "seq_len": 128, "phase": "decode"}
    source["benchmark_summary"] = {"summary": {"out_tokens": 9, "n_ok": 2}}
    source_path = tmp_path / "aggregate.json"
    output = tmp_path / "aggregate-case.json"
    source_path.write_text(json.dumps(source))
    assert sim_bridge.main([
        "export-sim-case", "--input", str(source_path),
        "--output", str(output),
    ]) == 2
    assert not output.exists()

    assert sim_bridge.main([
        "export-sim-case", "--input", str(source_path),
        "--output", str(output), "--diagnostic",
    ]) == 0
    case = json.loads(output.read_text())
    assert case["runtime"]["metadata"]["diagnostic_aggregate"]["out_tokens"] == 9
