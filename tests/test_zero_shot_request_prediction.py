"""Self-contained tests for per-launch TTFT forecast, T14 service routing, and evaluation join."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))

import zero_shot_client_capture as capture_api  # noqa: E402
import zero_shot_client_requests as client  # noqa: E402
import zero_shot_piecewise_validation as zsv  # noqa: E402
import zero_shot_request_prediction as prediction  # noqa: E402

KIMI4 = ROOT / "examples" / "structure" / "cases" / "decode-a3_kimi4_tp8_w4a8_c1.json"


@pytest.fixture
def campaign_fixture(tmp_path: Path):
    root = tmp_path / "rack06_campaign"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "bench_cell.py").write_text("# synthetic bench_cell\n", encoding="utf-8")
    (root / "cases").mkdir(parents=True)

    # 1. C=2 decode cell (dp=2, tp=8)
    c2_case = "kimi4_dp2tp8"
    c2_id = f"{c2_case}_dc_2k_c2"
    (root / "cases" / f"{c2_case}.json").write_text(
        json.dumps({"dp": 2, "tp": 8, "max_num_batched_tokens": 2048, "max_num_seqs": 32}),
        encoding="utf-8",
    )
    c2_meas = root / "out" / c2_case / "measured" / f"{c2_id}.json"
    c2_meas.parent.mkdir(parents=True)
    c2_meas.write_text(json.dumps({
        "tag": c2_id,
        "mode": "profile_decode",
        "started": "2026-11-08T10:00:00Z",
        "prompt_tokens": 2048,
        "shared_tokens": 1920,
        "max_tokens": 8,
        "concurrency": 2,
        "success": 2,
        "failed": 0,
        "first_token_latencies_s": [0.11, 0.12],
        "streams": [
            {"ok": True, "ttft_s": 0.11, "e2e_s": 0.25, "completion_tokens": 8, "chunks": 8},
            {"ok": True, "ttft_s": 0.12, "e2e_s": 0.26, "completion_tokens": 8, "chunks": 8},
        ],
    }), encoding="utf-8")
    c2_row = {
        "cell_id": c2_id,
        "dataset": "out",
        "phase": "decode",
        "model_case": str(KIMI4),
        "model_label": "kimi-k3-4layer",
        "prompt_tokens": 2048,
        "concurrency": 2,
        "max_tokens": 8,
        "tp": 8,
        "dp": 2,
        "ep": 1,
        "pp": 1,
    }

    # 2. C=4 multichunk cell (dp=2, tp=8, prompt=4096, budget=2048)
    c4_case = "kimi4_multi"
    c4_id = f"{c4_case}_dc_4k_c4"
    (root / "cases" / f"{c4_case}.json").write_text(
        json.dumps({"dp": 2, "tp": 8, "max_num_batched_tokens": 4096, "max_num_seqs": 32}),
        encoding="utf-8",
    )
    c4_meas = root / "out" / c4_case / "measured" / f"{c4_id}.json"
    c4_meas.parent.mkdir(parents=True)
    ttfts = [0.21, 0.22, 0.31, 0.32]
    c4_meas.write_text(json.dumps({
        "tag": c4_id,
        "mode": "profile_decode",
        "started": "2026-11-08T11:00:00Z",
        "prompt_tokens": 4096,
        "shared_tokens": 3968,
        "max_tokens": 8,
        "concurrency": 4,
        "success": 4,
        "failed": 0,
        "first_token_latencies_s": ttfts,
        "streams": [
            {"ok": True, "ttft_s": t, "e2e_s": t + 0.2, "completion_tokens": 8, "chunks": 8}
            for t in ttfts
        ],
    }), encoding="utf-8")
    c4_row = {
        "cell_id": c4_id,
        "dataset": "out",
        "phase": "decode",
        "model_case": str(KIMI4),
        "model_label": "kimi-k3-4layer",
        "prompt_tokens": 4096,
        "concurrency": 4,
        "max_tokens": 8,
        "tp": 8,
        "dp": 2,
        "ep": 1,
        "pp": 1,
    }
    capture_api._measured_index.cache_clear()
    return root, c2_row, c4_row


def test_t14_request_helper_consumes_real_shared_service_event() -> None:
    spec = zsv.CellSpec("probe", "unit", "prefill", KIMI4, "kimi-k3-4layer",
                        8, 1, 1, 8, 1, 1, 1)
    identity = SimpleNamespace(
        producer={"producer_sha256": "p", "ttft_boundary": "client"},
        original_row_sha256="r", started="s")
    declared = [{"key": "k0", "ordinal": 0, "prompt_tokens": 8,
                 "max_tokens": 1, "conditions": {}, "rack": None, "producer": None}]
    result = prediction._t14_request_forecast(
        spec, declared, [8], identity,
        {"schema": prediction.P9_SCHEMA, "cell_id": "probe", "status": "unavailable",
         "reason": None, "requests": [], "cell": {}, "summary": {}},
        0.0, [], 8)
    assert result["status"] == "forecast"
    assert result["cell"]["scheduling_model"] == "round_robin_fcfs"
    assert result["cell"]["scheduler_condition"] == "t14_shared_run_cohort"
    assert result["requests"][0]["predicted_ms"] > 0
    assert result["requests"][0]["absolute_finish_ms"] >= result["requests"][0]["predicted_ms"]
    assert result["cell"]["memory"]["status"] == "feasible"
    assert result["cell"]["execution"]["iterations"] >= 1
    assert result["requests"][0]["source"].endswith("T14_run_cohort_request_event")


def test_default_forecast_dispatches_to_t14_driver(campaign_fixture, monkeypatch: pytest.MonkeyPatch) -> None:
    root, c2_row, _ = campaign_fixture
    calls = []
    sentinel = {"schema": prediction.P9_SCHEMA, "cell_id": "x", "status": "forecast",
                "reason": None, "requests": [], "cell": {}, "summary": {}}

    def fake(spec, declared, prompts, identity, base, overhead, counterfactual, budget):
        calls.append((spec.cell_id, len(declared), list(prompts)))
        return sentinel

    monkeypatch.setattr(prediction, "_t14_request_forecast", fake)
    result = prediction.forecast_cell(c2_row, roots=[root])
    assert result is sentinel
    assert calls and calls[0] == (c2_row["cell_id"], 2, [2048, 2048])


def test_c2_forecast_and_evaluate_blindness(campaign_fixture, tmp_path: Path) -> None:
    root, c2_row, _ = campaign_fixture
    forecast = prediction.forecast_cell(c2_row, roots=[root])
    assert forecast["schema"] == prediction.P9_SCHEMA
    assert forecast["status"] == "forecast", forecast.get("reason")
    assert len(forecast["requests"]) == 2
    assert [item["launch_ordinal"] for item in forecast["requests"]] == [0, 1]
    assert all(item["actual_ms"] is None and item["predicted_ms"] > 0 for item in forecast["requests"])
    assert all(item["host_overhead_ms"] == 0.0 and item["host_overhead_status"] == "absent_assumed_zero"
               for item in forecast["requests"])
    assert forecast["cell"]["scheduling_model"] == "round_robin_fcfs"
    assert forecast["cell"]["actual_scheduler_observed"] is False
    assert forecast["summary"]["mean_preserved"] is True

    evaluated = prediction.evaluate_cell(c2_row, roots=[root])
    assert evaluated["summary"]["observed"] == 2
    assert evaluated["summary"]["missing"] == 0
    for before, after in zip(forecast["requests"], evaluated["requests"]):
        assert before["predicted_ms"] == after["predicted_ms"]
        assert after["actual_ms"] is not None and after["actual_ms"] > 0
        assert after["signed_error"] is not None

    # Removing measured outcomes keeps forecast identical and leaves actual_ms=None
    stripped = tmp_path / "rack06_stripped"
    stripped.mkdir(parents=True, exist_ok=True)
    (stripped / "bin").symlink_to(root / "bin")
    (stripped / "cases").symlink_to(root / "cases")
    orig_meas = root / "out" / "kimi4_dp2tp8" / "measured" / f"{c2_row['cell_id']}.json"
    dest_meas = stripped / "out" / "kimi4_dp2tp8" / "measured" / f"{c2_row['cell_id']}.json"
    dest_meas.parent.mkdir(parents=True)
    rec = json.loads(orig_meas.read_text(encoding="utf-8"))
    rec.pop("first_token_latencies_s", None)
    rec.pop("streams", None)
    dest_meas.write_text(json.dumps(rec), encoding="utf-8")
    capture_api._measured_index.cache_clear()
    missing = prediction.forecast_cell(c2_row, roots=[stripped])
    assert [item["predicted_ms"] for item in missing["requests"]] == [
        item["predicted_ms"] for item in forecast["requests"]
    ]
    eval_missing = prediction.evaluate_cell(c2_row, roots=[stripped])
    assert eval_missing["summary"]["missing"] == 2
    assert all(item["actual_ms"] is None for item in eval_missing["requests"])


def test_distinct_q_chunk_budget_and_missing_declarations(campaign_fixture) -> None:
    root, c2_row, c4_row = campaign_fixture
    absent = prediction.forecast_cell({"cell_id": "no-such-cell", "phase": "decode"}, roots=[root])
    assert absent["status"] == "unavailable"

    clean = prediction.forecast_cell(c2_row, roots=[root])
    base = [dict(item) for item in clean["requests"]]

    def _with_q(item: dict, q: int) -> dict:
        out = dict(item, prompt_tokens=q)
        out["key"] = out["key"].replace("|p=2048|", f"|p={q}|")
        return out

    distinct = prediction.forecast_cell(
        c2_row, roots=[root], declarations=[_with_q(base[0], 512), _with_q(base[1], 1024)])
    assert distinct["status"] == "forecast"
    assert distinct["requests"][0]["predicted_ms"] != distinct["requests"][1]["predicted_ms"]

    # Chunk budget > prompt_tokens is a noop; smaller chunk budget increases multichunk TTFT
    one_2048 = prediction.forecast_cell(
        c2_row, roots=[root], declarations=[dict(item, chunk_budget=2048) for item in base])
    one_4096 = prediction.forecast_cell(
        c2_row, roots=[root], declarations=[dict(item, chunk_budget=4096) for item in base])
    assert one_2048["requests"][0]["predicted_ms"] == pytest.approx(one_4096["requests"][0]["predicted_ms"])

    c4_clean = prediction.forecast_cell(c4_row, roots=[root])
    c4_base = [dict(item) for item in c4_clean["requests"]]
    m1024 = prediction.forecast_cell(
        c4_row, roots=[root], declarations=[dict(item, chunk_budget=1024) for item in c4_base])
    m4096 = prediction.forecast_cell(
        c4_row, roots=[root], declarations=[dict(item, chunk_budget=4096) for item in c4_base])
    assert m1024["status"] == m4096["status"] == "forecast"
    assert m1024["requests"][0]["predicted_ms"] != pytest.approx(m4096["requests"][0]["predicted_ms"])


def test_declaration_validation_counterfactuals_and_h3_scheduler(
    campaign_fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, c2_row, c4_row = campaign_fixture
    clean = prediction.forecast_cell(c4_row, roots=[root])
    decl = [dict(item) for item in clean["requests"]]
    foreign_start = prediction.forecast_cell(c2_row, roots=[root])["requests"][0]["conditions"]["started"]
    cases = {
        "semantic_key": [{**item, "key": item["key"].replace("|ordinal=0|", "|ordinal=9|")} if i == 0 else item
                         for i, item in enumerate(decl)],
        "context": [dict(item, key=item["key"].replace(item["conditions"]["started"], foreign_start))
                    for item in decl],
        "clock": [{**item, "conditions": {**item["conditions"], "ttft_boundary": "foreign"}}
                  for item in decl],
        "rack_suffix": [{**item, "key": item["key"] + ":other"} if i == 0 else item
                        for i, item in enumerate(decl)],
        "ordinal": [{**item, "ordinal": (item["ordinal"] + 1) % 4} for item in decl],
    }
    for name, mutated in cases.items():
        res = prediction.forecast_cell(c4_row, roots=[root], declarations=mutated)
        assert res["status"] == "unavailable", name

    restored = prediction.forecast_cell(c4_row, roots=[root], declarations=list(reversed(decl)))
    assert restored["status"] == "forecast"
    assert [item["launch_ordinal"] for item in restored["requests"]] == [0, 1, 2, 3]

    # Shuffled capture declarations evaluate cleanly; counterfactual budget & host_overhead withhold strict grading
    cap = client.client_capture(c4_row, roots=[root])
    shuffled_eval = prediction.evaluate_cell(c4_row, roots=[root], declarations=list(reversed(cap.declarations)))
    assert shuffled_eval["summary"]["observed"] == 4

    source = prediction.source_declarations(c4_row, roots=[root])
    bad_prompt = {**c4_row, "prompt_tokens": 1025}
    assert prediction.evaluate_cell(bad_prompt, roots=[root])["reason"] == "row_prompt_tokens_mismatch"
    assert prediction.evaluate_cell(bad_prompt, roots=[root], declarations=source)["reason"] == "row_prompt_tokens_mismatch"

    cf_budget = prediction.evaluate_cell(
        c4_row, roots=[root], declarations=[dict(item, chunk_budget=1024) for item in source])
    assert cf_budget["summary"]["observed"] == 0
    assert all(item["join_status"] == "counterfactual_no_grade" for item in cf_budget["requests"])

    cf_host = prediction.evaluate_cell(c4_row, roots=[root], host_overhead_ms=125.0)
    assert cf_host["summary"]["grade_eligible"] is False
    assert all(item["join_status"] == "counterfactual_no_grade" for item in cf_host["requests"])
    assert all(
        item["predicted_ms"] - base_item["predicted_ms"] == pytest.approx(125.0)
        for item, base_item in zip(cf_host["requests"], shuffled_eval["requests"])
    )

    view = prediction.forecast_view(c2_row, roots=[root])
    assert view["schema"] == prediction.P12_SCHEMA and view["summary"]["observed"] == 2

    # H3 conditional open scheduler diagnostics and error handling
    h3 = prediction.evaluate_cell(c4_row, roots=[root], scheduler="h3_open")
    assert h3["status"] == "forecast"
    assert h3["cell"]["model_condition"] is True
    assert h3["cell"]["grade_eligible"] is False and h3["cell"]["diagnostic_eligible"] is True
    assert h3["summary"]["strict_graded"] == 0 and h3["summary"]["diagnostic_observed"] == 4

    one_seq = prediction.forecast_cell(c4_row, roots=[root], scheduler="h3_open", max_num_seqs=1)
    many_seq = prediction.forecast_cell(c4_row, roots=[root], scheduler="h3_open", max_num_seqs=32)
    assert [x["predicted_ms"] for x in one_seq["requests"]] != [x["predicted_ms"] for x in many_seq["requests"]]
    assert prediction.forecast_cell(c4_row, roots=[root], scheduler="not_a_scheduler")["status"] == "unavailable"

    monkeypatch.setitem(sys.modules, "mindie_sim.prediction.piecewise.open_prefill_scheduler", None)
    unavail = prediction.forecast_cell(c4_row, roots=[root], scheduler="h3_open")
    assert unavail["status"] == "unavailable"
    assert unavail["reason"].startswith("h3_or_kb_adapter_unavailable")
