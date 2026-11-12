"""Focused tests for P9 per-launch TTFT forecast and evaluation join."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))

import zero_shot_client_capture as capture_api  # noqa: E402
import zero_shot_client_requests as client  # noqa: E402
import zero_shot_request_prediction as prediction  # noqa: E402

CELLS = Path("/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl")


def _row(cell_id: str) -> dict:
    return next(item for item in map(json.loads, CELLS.open())
                if item.get("cell_id") == cell_id)


def test_c2_forecast_shape_no_observed_and_mean_preserved():
    result = prediction.forecast_cell(_row("dsv41_dp16tp1ep16_dc_2k_c2"))
    assert result["schema"] == prediction.P9_SCHEMA
    assert result["status"] == "forecast", result.get("reason")
    assert len(result["requests"]) == 2
    assert [item["launch_ordinal"] for item in result["requests"]] == [0, 1]
    assert all(item["actual_ms"] is None for item in result["requests"])
    assert all(item["predicted_ms"] > 0 for item in result["requests"])
    assert all(item["host_overhead_ms"] == 0.0 for item in result["requests"])
    assert all(item["host_overhead_status"] == "absent_assumed_zero"
               for item in result["requests"])
    assert result["cell"]["scheduling_model"] == "round_robin_fcfs"
    assert result["cell"]["actual_scheduler_observed"] is False
    assert result["summary"]["mean_preserved"] is True


def test_evaluate_joins_actual_but_does_not_change_forecast():
    row = _row("dsv41_dp16tp1ep16_dc_2k_c2")
    forecast = prediction.forecast_cell(row)
    evaluated = prediction.evaluate_cell(row)
    assert evaluated["summary"]["observed"] == 2
    assert evaluated["summary"]["missing"] == 0
    for before, after in zip(forecast["requests"], evaluated["requests"]):
        assert before["predicted_ms"] == after["predicted_ms"]
        assert after["actual_ms"] is not None and after["actual_ms"] > 0
        assert after["signed_error"] is not None


def test_removing_measured_outcomes_keeps_forecast_unchanged(tmp_path):
    row = _row("dsv41_dp16tp1ep16_dc_2k_c2")
    clean = prediction.forecast_cell(row)
    capture = client.client_capture(row)
    raw_path = Path(capture.measured_path)
    root = raw_path.parents[3]
    case = raw_path.parents[2]
    temp = tmp_path / "root"
    case_out = temp / "out" / case.name
    measured = case_out / "measured"
    measured.mkdir(parents=True)
    (temp / "bin").symlink_to(root / "bin")
    (temp / "cases").symlink_to(root / "cases")
    for item in case.iterdir():
        if item.name != "measured":
            (case_out / item.name).symlink_to(item)
    record = json.loads(raw_path.read_text())
    record.pop("first_token_latencies_s", None)
    record.pop("streams", None)
    (measured / raw_path.name).write_text(json.dumps(record), encoding="utf-8")
    capture_api._measured_index.cache_clear()
    missing = prediction.forecast_cell(row, roots=[temp])
    assert missing["status"] == "forecast", missing.get("reason")
    assert len(missing["requests"]) == 2
    assert [item["predicted_ms"] for item in missing["requests"]] == [
        item["predicted_ms"] for item in clean["requests"]]
    evaluated = prediction.evaluate_cell(row, roots=[temp])
    assert all(item["actual_ms"] is None for item in evaluated["requests"])
    assert evaluated["summary"]["missing"] == 2


def test_distinct_q_controls_and_genuine_tie():
    row = _row("dsv41_dp16tp1ep16_dc_2k_c2")
    clean = prediction.forecast_cell(row)
    base = [dict(item) for item in clean["requests"]]
    tied = [dict(base[0]), dict(base[1])]
    tied_result = prediction.forecast_cell(row, declarations=tied)
    assert tied_result["status"] == "forecast"
    assert tied_result["requests"][0]["predicted_ms"] == tied_result["requests"][1]["predicted_ms"]
    def _with_q(item, q):
        out = dict(item, prompt_tokens=q)
        out["key"] = out["key"].replace("|p=2048|", f"|p={q}|")
        return out
    distinct = [_with_q(base[0], 512), _with_q(base[1], 1024)]
    distinct_result = prediction.forecast_cell(row, declarations=distinct)
    assert distinct_result["status"] == "forecast"
    assert distinct_result["requests"][0]["predicted_ms"] != distinct_result["requests"][1]["predicted_ms"]


def test_missing_declarations_do_not_fabricate():
    monkey_row = {"cell_id": "no-such-cell", "phase": "decode"}
    result = prediction.forecast_cell(monkey_row)
    assert result["status"] == "unavailable"
    assert result["reason"] in {"declarations_absent", "spec_unavailable:KeyError:'no-such-cell'"} or result["reason"].startswith("spec_unavailable")


def test_chunk_budget_noop_single_and_positive_multichunk_context():
    row = _row("dsv41_dp16tp1ep16_dc_2k_c2")
    clean = prediction.forecast_cell(row)
    base = [dict(item) for item in clean["requests"]]
    one_2048 = prediction.forecast_cell(
        row, declarations=[dict(item, chunk_budget=2048) for item in base])
    one_4096 = prediction.forecast_cell(
        row, declarations=[dict(item, chunk_budget=4096) for item in base])
    assert one_2048["requests"][0]["predicted_ms"] == one_4096["requests"][0]["predicted_ms"]

    mixed = _row("dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8")
    mixed_clean = prediction.forecast_cell(mixed)
    mixed_base = [dict(item) for item in mixed_clean["requests"]]
    m2048 = prediction.forecast_cell(
        mixed, declarations=[dict(item, chunk_budget=2048) for item in mixed_base])
    m8192 = prediction.forecast_cell(
        mixed, declarations=[dict(item, chunk_budget=8192) for item in mixed_base])
    assert m2048["status"] == m8192["status"] == "forecast"
    assert m2048["requests"][0]["predicted_ms"] > m8192["requests"][0]["predicted_ms"]

    import dataclasses
    import zero_shot_piecewise_validation as zsv
    spec = zsv.cell_from_dict(mixed).spec
    prefill = dataclasses.replace(spec, phase="prefill", prompt_tokens=8192,
                                  concurrency=1, max_tokens=1,
                                  sequences_per_replica=1, tokens_per_sequence=0)
    from zero_shot_chunk_pricing import predict_chunk
    bodies = [predict_chunk(prefill, 512, end).prefill_body_ms
              for end in (512, 2048, 8192)]
    assert bodies[0] < bodies[1] < bodies[2]


def test_semantic_key_mismatch_is_not_bound():
    row = _row("dsv41_dp16tp1ep16_dc_2k_c2")
    clean = prediction.forecast_cell(row)
    bad = [dict(item) for item in clean["requests"]]
    bad[0]["key"] = bad[0]["key"].replace("|ordinal=0|", "|ordinal=9|")
    result = prediction.forecast_cell(row, declarations=bad)
    assert result["status"] == "unavailable"
    assert result["reason"] in {"declaration_key_mismatch", "semantic_key_mismatch"}


def test_negative_key_context_rack_clock_ordinal_and_reverse():
    row = _row("dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8")
    clean = prediction.forecast_cell(row)
    decl = [dict(item) for item in clean["requests"]]
    foreign_start = prediction.forecast_cell(
        _row("dsv41_dp16tp1ep16_dc_2k_c2"))["requests"][0]["conditions"]["started"]
    cases = {
        "context": [dict(item, key=item["key"].replace(
            item["conditions"]["started"], foreign_start)) for item in decl],
        "clock": [{**item, "conditions": {**item["conditions"],
                                         "ttft_boundary": "foreign"}} for item in decl],
        "rack_suffix": [{**item, "key": item["key"] + ":other"} if i == 0 else item
                        for i, item in enumerate(decl)],
        "ordinal": [{**item, "ordinal": (item["ordinal"] + 1) % 8} for item in decl],
    }
    for name, mutated in cases.items():
        result = prediction.forecast_cell(row, declarations=mutated)
        assert result["status"] == "unavailable", name
        assert result["reason"].startswith("declaration_"), (name, result["reason"])
    restored = prediction.forecast_cell(row, declarations=list(reversed(decl)))
    assert restored["status"] == "forecast"
    assert [item["launch_ordinal"] for item in restored["requests"]] == list(range(8))


def test_source_objects_shuffled_budget_counterfactual_and_view():
    row = _row("dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8")
    source = prediction.source_declarations(row)
    assert len(source) == 8 and all(item.get("key") for item in source)
    capture = client.client_capture(row)
    shuffled = list(reversed(capture.declarations))
    result = prediction.evaluate_cell(row, declarations=shuffled)
    assert result["status"] == "forecast"
    assert result["summary"]["observed"] == 8
    assert [item["launch_ordinal"] for item in result["requests"]] == list(range(8))

    # Same explicit physical budget for all ordinals: forecast changes, no grading.
    changed = prediction.evaluate_cell(
        row, declarations=[dict(item, chunk_budget=2048) for item in source])
    assert changed["status"] == "forecast"
    assert changed["summary"]["observed"] == 0
    assert all(item["join_status"] == "counterfactual_no_grade"
               for item in changed["requests"])
    assert all(item["predicted_ms"] != source_clean
               for item, source_clean in zip(
                   changed["requests"],
                   prediction.forecast_cell(row)["requests"]))

    view = prediction.forecast_view(_row("dsv41_dp16tp1ep16_dc_2k_c2"))
    assert view["schema"] == prediction.P12_SCHEMA
    assert all(item.get("key") for item in view["requests"])
    assert view["summary"]["observed"] == 2


def test_default_and_explicit_row_prompt_use_same_source_normalization():
    row = _row("dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8")
    source = prediction.source_declarations(row)
    bad_row = {**row, "prompt_tokens": 1025}
    default = prediction.evaluate_cell(bad_row)
    explicit = prediction.evaluate_cell(bad_row, declarations=source)
    assert default["status"] == explicit["status"] == "unavailable"
    assert default["reason"] == explicit["reason"] == "row_prompt_tokens_mismatch"
    assert default.get("requests", []) == explicit.get("requests", []) == []


def test_positive_host_overhead_is_scenario_not_original_grade():
    row = _row("dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8")
    base = prediction.evaluate_cell(row)
    assert base["summary"]["observed"] == 8
    scenario = prediction.evaluate_cell(row, host_overhead_ms=125.0)
    assert scenario["status"] == "forecast"
    assert scenario["summary"]["observed"] == 0
    assert scenario["summary"]["grade_eligible"] is False
    assert scenario["cell"]["scenario"] == "host_overhead_scenario"
    assert scenario["cell"]["host_overhead_grade_eligible"] is False
    assert all(item["join_status"] == "counterfactual_no_grade"
               for item in scenario["requests"])
    assert all(item["predicted_ms"] - baseline["predicted_ms"] == 125.0
               for item, baseline in zip(scenario["requests"], base["requests"]))


def test_h3_conditional_is_diagnostic_and_default_is_unchanged():
    qwen = _row("smoke_qwen36_single_dc_4k_c8")
    default = prediction.evaluate_cell(qwen)
    assert default["summary"]["observed"] == 8
    assert default["summary"]["strict_graded"] == 8
    assert default["summary"]["score_scope"] == "original"

    h3 = prediction.evaluate_cell(qwen, scheduler="h3_open")
    assert h3["status"] == "forecast"
    assert h3["cell"]["model_condition"] is True
    assert h3["cell"]["score_scope"] == "conditional_batch_model"
    assert h3["cell"]["h3_steps"] > 0
    assert h3["cell"]["h3_body_calls"] and all(v > 0 for v in h3["cell"]["h3_body_calls"])
    assert h3["cell"]["grade_eligible"] is False
    assert h3["cell"]["diagnostic_eligible"] is True
    assert h3["summary"]["strict_graded"] == 0
    assert h3["summary"]["diagnostic_observed"] == 8
    assert all(item["join_status"] == "conditional_model_diagnostic"
               for item in h3["requests"])
    assert [item["launch_ordinal"] for item in h3["requests"]] == list(range(8))

    c2 = prediction.evaluate_cell(_row("dsv41_dp16tp1ep16_dc_2k_c2"),
                                  scheduler="h3_open")
    assert c2["summary"]["observed"] == 2
    assert c2["summary"]["diagnostic_observed"] == 2
    assert c2["summary"]["strict_graded"] == 0


def test_h3_maxseq_controls_and_missing_condition_fail_explicitly():
    qwen = _row("smoke_qwen36_single_dc_4k_c8")
    one = prediction.forecast_cell(qwen, scheduler="h3_open", max_num_seqs=1)
    many = prediction.forecast_cell(qwen, scheduler="h3_open", max_num_seqs=32)
    assert one["status"] == many["status"] == "forecast"
    assert [x["predicted_ms"] for x in one["requests"]] != [
        x["predicted_ms"] for x in many["requests"]]
    bad = prediction.forecast_cell(qwen, scheduler="not_a_scheduler")
    assert bad["status"] == "unavailable"
    assert bad["reason"].startswith("scheduler_condition_unsupported")


def test_missing_h3_or_kb_adapter_is_explicit(monkeypatch):
    import sys
    qwen = _row("smoke_qwen36_single_dc_4k_c8")
    monkeypatch.setitem(
        sys.modules,
        "mindie_sim.prediction.piecewise.open_prefill_scheduler", None)
    result = prediction.forecast_cell(qwen, scheduler="h3_open")
    assert result["status"] == "unavailable"
    assert result["reason"].startswith("h3_or_kb_adapter_unavailable")


def test_h3_declared_arrival_order_and_q_kv_controls():
    qwen = _row("smoke_qwen36_single_dc_4k_c8")
    forward = prediction.forecast_cell(
        qwen, scheduler="h3_open", arrival_order=list(range(8)))
    reverse = prediction.forecast_cell(
        qwen, scheduler="h3_open", arrival_order=list(range(7, -1, -1)))
    assert forward["status"] == reverse["status"] == "forecast"
    assert forward["cell"]["model_condition"] is True
    assert reverse["cell"]["h3_steps"] >= 1
    # q/KV controls are real body-batch calls, not scalar substitutions.
    import zero_shot_chunk_pricing as cp
    import zero_shot_piecewise_validation as zsv
    import dataclasses
    spec = zsv.cell_from_dict(qwen).spec
    prefill = dataclasses.replace(spec, phase="prefill", prompt_tokens=8192,
                                  concurrency=1, max_tokens=1,
                                  sequences_per_replica=1, tokens_per_sequence=0)
    a = cp.predict_chunk_batch(prefill, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1}])
    b = cp.predict_chunk_batch(prefill, [
        {"ordinal": 0, "q_len": 512, "kv_end": 8192, "phase": "prefill", "seq": 1}])
    c = cp.predict_chunk_batch(prefill, [
        {"ordinal": 0, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1},
        {"ordinal": 1, "q_len": 512, "kv_end": 512, "phase": "prefill", "seq": 1}])
    assert a["total_ms"] != b["total_ms"]
    assert c["total_ms"] > a["total_ms"]
