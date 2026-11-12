"""Request-forecast binding. Errors come from the scorer, not from prose checks."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import fleet_capture_observations as observations  # noqa: E402
import hf_benchmark_gate as gate  # noqa: E402
import hf_profiling_benchmark as benchmark  # noqa: E402

CELL = "unit-cell"
CLOCK = "client_send_to_first_sse_with_choices_may_empty"
OTHER_CLOCK = "client_send_to_first_nonempty_text_or_terminal_fallback"
SHA = "a" * 64
OTHER_SHA = "b" * 64
SAVED = Path("/tmp/mindie-7337-20261111-1457/obs-r3/cg4-normal-small.json")
CELLS = Path("/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl")


@pytest.fixture(autouse=True)
def _isolated_homes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "cg5-home"
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(root / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(root / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(root / "diag"))
    os.environ["HOME"] = str(root)


def _key(ordinal: int, prompt: int = 128) -> str:
    return (
        f"{CELL}|ordinal={ordinal}|ctx=2026-11-07T00:00:00Z|C=2|p={prompt}"
        f"|o=16|mix=base|rack=rack06"
    )


def _interface(clock: str = CLOCK, metric: str = "") -> dict:
    requests = []
    for ordinal, ttft_s in ((0, 0.100), (1, 0.200)):
        item = {
            "key": _key(ordinal),
            "launch_ordinal": ordinal,
            "ttft_s": ttft_s,
            "ttft_boundary": clock,
        }
        if metric:
            item["metric"] = metric
        requests.append(item)
    return {
        "cell": {
            "cell_id": CELL,
            "phase": "decode",
            "rack": "rack06",
            "producer_sha256": SHA,
            "concurrency": 2,
        },
        "requests": requests,
        "declarations": [
            {"key": _key(0), "ordinal": 0, "ttft_boundary": clock},
            {"key": _key(1), "ordinal": 1, "ttft_boundary": clock},
        ],
    }


def _prediction(samples: dict[str, float], sha: str = SHA) -> dict:
    return {
        "status": "modeled",
        "prediction_boundary": "native_client_request",
        "capture_id": CELL,
        "phase": "decode",
        "producer_sha256": sha,
        "boundary_samples": samples,
    }


def _score(interface: dict, prediction: dict) -> dict:
    return gate.score_l4_bundle(
        {"cell_id": CELL, "phase": "decode", "hardware_tier": "A5"},
        {"eligible": False, "interface": interface, "prediction": prediction},
        tier="A5",
    )


def test_same_source_keys_keep_per_id_errors_under_reorder_and_removal() -> None:
    samples = {_key(0): 112.0, _key(1): 190.0}
    forward = _score(_interface(), _prediction(samples))
    assert forward["comparison"] == "compared"
    assert forward["comparison_reason"] == "exact_keyed_samples"
    assert forward["producer_clock_status"] == "matched"
    assert forward["tpot_domain"] == "not_scored_on_request_ttft"
    assert forward["key_denominator"] == 2
    assert forward["per_key_errors"][_key(0)] == pytest.approx(0.12)
    assert forward["per_key_errors"][_key(1)] == pytest.approx(-0.05)
    assert forward["passed_10pct"] is False

    reversed_samples = {_key(1): 190.0, _key(0): 112.0}
    backward = _score(_interface(), _prediction(reversed_samples))
    assert backward["per_key_errors"] == pytest.approx(forward["per_key_errors"])

    removed = _score(_interface(), _prediction({_key(0): 112.0}))
    assert removed["comparison"] == "invalid"
    assert removed["comparison_reason"] == "sample_key_population_mismatch"
    assert _key(1) in removed["missing_keys"]
    assert removed["key_denominator"] == 2
    assert removed["passed_10pct"] is False
    assert removed["per_key_errors"][_key(0)] == pytest.approx(0.12)
    assert _key(1) not in removed["per_key_errors"]


def test_tpot_and_inter_token_are_not_ttft_pairs() -> None:
    tpot = _score(_interface(clock="per_request_tpot"), _prediction({_key(0): 100.0, _key(1): 200.0}))
    assert tpot["comparison"] != "compared"
    assert tpot["passed_10pct"] is False
    assert tpot["request_ttft_incompatible"] == 2
    assert tpot["per_key_errors"] == {}
    assert tpot["key_denominator"] == 2

    metric = _score(
        _interface(metric="inter_token_latency"),
        _prediction({_key(0): 100.0, _key(1): 200.0}),
    )
    assert metric["passed_10pct"] is False
    assert metric["request_ttft_incompatible"] == 2
    assert metric["per_key_errors"] == {}

    observation = {
        "capture": {"capture_id": CELL, "phase": "decode", "hardware_tier": "A5"},
        "measurements": {"native_client_request": {
            "status": "measured",
            "phase": "decode",
            "samples_basis": "per_request_inter_token_interval",
            "samples": [{"key": _key(0), "observed_ms": 100.0, "phase": "decode"}],
        }},
    }
    prediction = {
        "status": "modeled",
        "prediction_boundary": "native_client_request",
        "hardware_tier": "A5",
        "phase": "decode",
        "capture_id": CELL,
        "boundary_samples": {_key(0): 100.0},
    }
    basis = gate.score_fleet_row(
        {"capture_id": CELL, "phase": "decode", "hardware_tier": "A5"},
        observation,
        prediction,
    )
    assert basis["comparison_reason"] == "request_boundary_not_per_request"
    assert basis["passed_10pct"] is False


def test_bad_producer_sha_is_not_a_pass_and_equal_values_are_not_a_repeated_aggregate() -> None:
    bad = _score(_interface(), _prediction({_key(0): 100.0, _key(1): 200.0}, sha="b" * 64))
    assert bad["comparison"] == "invalid"
    assert bad["comparison_reason"] == "producer_sha256_mismatch"
    assert bad["passed_10pct"] is False
    assert bad["key_denominator"] == 2
    assert bad["per_key_errors"] == {}

    tied = _score(_interface(), _prediction({_key(0): 100.0, _key(1): 100.0}))
    assert tied["comparison"] == "compared"
    assert tied["per_key_errors"][_key(0)] == pytest.approx(0.0)
    assert tied["per_key_errors"][_key(1)] == pytest.approx(-0.5)
    assert len(tied["per_key_errors"]) == 2


def test_forecast_bind_uses_each_row_and_ignores_actuals_and_the_cell_mean() -> None:
    declarations = []
    requests = []
    for ordinal, prompt, rank in ((0, 2048, 0), (1, 2048, 1)):
        key = _key(ordinal, prompt)
        declarations.append({
            "key": key, "cell_id": CELL, "ordinal": ordinal, "phase": "decode",
            "prompt_tokens": prompt, "max_tokens": 16, "mix_class": "base",
            "rack": "rack06", "producer": "rack06_any_choices_sse", "concurrency": 2,
        })
        requests.append({
            "key": key, "semantic_key": key, "semantic_key_status": "verified",
            "cell_id": CELL, "phase": "decode", "launch_ordinal": ordinal,
            "prompt_tokens": prompt, "max_tokens": 16, "mix_class": "base",
            "rack": "rack06", "producer": "rack06_any_choices_sse", "concurrency": 2,
            "predicted_ms": 50.0, "own_body_ms": 40.0 + ordinal, "queue_wait_ms": float(ordinal),
            "rank_assignment": rank, "rank_queue_index": 0,
            "actual_ms": 1.0, "signed_error": 0.0, "unsigned_error": 0.0,
        })
    requests.append({
        "key": _key(2, 2048), "semantic_key": _key(2, 2048), "semantic_key_status": "mismatch",
        "cell_id": CELL, "phase": "decode", "launch_ordinal": 2, "prompt_tokens": 2048,
        "max_tokens": 16, "mix_class": "base", "rack": "rack06",
        "producer": "rack06_any_choices_sse", "concurrency": 2, "predicted_ms": 50.0,
    })
    forecast = {
        "status": "forecast",
        "schema": "mindie-profiler-request-ttft-prediction/1",
        "cell": {
            "phase": "decode", "model_case": "/tmp/model", "mean_forecast_ms": 1.0,
            "host_overhead_status": "absent_assumed_zero",
            "actual_scheduler_observed": False,
            "chunk_budget": 8192,
        },
        "requests": list(reversed(requests)),
    }
    bound = benchmark._bind_request_forecast(CELL, "decode", declarations, [], SHA, forecast)
    assert bound["prediction"]["boundary_samples"] == {_key(0, 2048): 50.0, _key(1, 2048): 50.0}
    assert 1.0 not in bound["prediction"]["boundary_samples"].values()
    assert bound["forecast_unbound_keys"] == [_key(2, 2048)]
    ranks = [item["rank_assignment"] for item in bound["request_forecasts"]]
    assert ranks == [1, 0]
    assert "actual_ms" not in bound["prediction"]
    assert bound["forecast_assumptions"]["priced_by"] == "forecast_cell"
    assert bound["forecast_assumptions"]["mean_forecast_ms"] == 1.0


def _dataset(root: Path) -> Path:
    data = root / "data"
    data.mkdir(parents=True)
    zs = b'{"cell_id":"c2","phase":"decode"}\n'
    fleet = b""
    (data / "zero_shot_l1_l4_cells.jsonl").write_bytes(zs)
    (data / "fleet_captures.jsonl").write_bytes(fleet)
    import gzip
    (data / "zero_shot_l1_l4_cells.jsonl.gz").write_bytes(gzip.compress(zs))
    (data / "fleet_captures.jsonl.gz").write_bytes(gzip.compress(fleet))
    return root


def test_targeted_and_full_both_call_the_request_pair(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake(row, price=True):
        calls.append(str(row.get("cell_id")))
        return {"eligible": False, "reason": "stub", "streams": 0, "notes": ()}

    monkeypatch.setattr(benchmark, "_zero_shot_l4_pair", fake)
    monkeypatch.setattr(benchmark, "_collect_structure_suites", lambda: ([], set()))
    monkeypatch.setattr(benchmark, "_zero_shot_timetables", lambda row: [])
    monkeypatch.setattr(observations, "configure_observation_roots", lambda **_kwargs: None)
    dataset = _dataset(tmp_path / "mini")
    targeted = benchmark.evaluate_dataset(dataset, inventory="targeted", summary_dir=tmp_path / "targeted")
    full = benchmark.evaluate_dataset(dataset, inventory="full", full_population=True, summary_dir=tmp_path / "full")
    assert calls == ["c2", "c2"]
    assert targeted["inventory"] == "targeted"
    assert full["inventory"] == "full"
    assert targeted["strict_global_pass"] is False
    assert full["totals"]["fleet_captures"] == 0
    l4 = json.loads((tmp_path / "targeted" / "zs_l4_per_id.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert l4["capture_id"] == "c2"
    assert l4["key_denominator"] == 0 or l4["comparison_reason"]


def _forecast_row(ordinal: int, predicted: float, *, sha: str = SHA, clock: str = CLOCK) -> dict:
    key = _key(ordinal)
    return {
        "key": key,
        "semantic_key": key,
        "semantic_key_status": "verified",
        "cell_id": CELL,
        "phase": "decode",
        "launch_ordinal": ordinal,
        "prompt_tokens": 128,
        "max_tokens": 16,
        "mix_class": "base",
        "rack": "rack06",
        "producer": "rack06_any_choices_sse",
        "producer_sha256": sha,
        "concurrency": 2,
        "predicted_ms": predicted,
        "own_body_ms": predicted,
        "queue_wait_ms": 0.0,
        "rank_assignment": ordinal,
        "rank_queue_index": 0,
    }


def _declarations() -> list[dict]:
    rows = []
    for ordinal in (0, 1):
        rows.append({
            "key": _key(ordinal),
            "cell_id": CELL,
            "ordinal": ordinal,
            "phase": "decode",
            "prompt_tokens": 128,
            "max_tokens": 16,
            "mix_class": "base",
            "rack": "rack06",
            "producer": "rack06_any_choices_sse",
            "concurrency": 2,
        })
    return rows


def _bind(forecast: dict, witness: str = SHA) -> dict:
    return benchmark._bind_request_forecast(
        CELL, "decode", _declarations(), [], witness, forecast,
    )


def test_forecast_clock_and_producer_are_not_replaced_by_the_observer() -> None:
    forecast = {
        "status": "forecast",
        "schema": "mindie-profiler-request-ttft-prediction/1",
        "cell": {
            "phase": "decode",
            "model_case": "/tmp/model",
            "client_boundary": CLOCK,
            "producer_boundary": CLOCK,
            "producer_sha256": SHA,
            "host_overhead_status": "absent_assumed_zero",
            "host_overhead_ms": 0.0,
            "actual_scheduler_observed": False,
        },
        "requests": [_forecast_row(0, 112.0), _forecast_row(1, 190.0)],
    }
    bound = _bind(forecast, witness=OTHER_SHA)
    assert bound["prediction"]["producer_sha256"] == SHA
    assert bound["prediction"]["ttft_boundary"] == CLOCK
    assert bound["forecast_assumptions"]["host_overhead_status"] == "absent_assumed_zero"
    assert bound["forecast_assumptions"]["host_overhead_ms"] is None
    kept = _score(_interface(), bound["prediction"])
    assert kept["comparison"] == "compared"
    assert kept["producer_clock_status"] == "matched"
    assert kept["per_key_errors"][_key(0)] == pytest.approx(0.12)

    foreign_clock = json.loads(json.dumps(forecast))
    foreign_clock["cell"]["client_boundary"] = OTHER_CLOCK
    foreign_clock["cell"]["producer_boundary"] = CLOCK
    rejected_clock = _bind(foreign_clock, witness=SHA)
    assert rejected_clock["prediction"]["ttft_boundary"] == OTHER_CLOCK
    assert "boundary_samples" not in rejected_clock["prediction"]
    scored_clock = _score(_interface(), rejected_clock["prediction"])
    assert scored_clock["comparison"] != "compared"
    assert scored_clock["key_matched"] == 0
    assert scored_clock["passed_10pct"] is False
    assert scored_clock["per_key_errors"] == {}

    foreign_sha = json.loads(json.dumps(forecast))
    foreign_sha["cell"]["producer_sha256"] = OTHER_SHA
    rejected_sha = _bind(foreign_sha, witness=SHA)
    assert rejected_sha["prediction"]["producer_sha256"] == OTHER_SHA
    assert "boundary_samples" not in rejected_sha["prediction"]
    scored_sha = _score(_interface(), rejected_sha["prediction"])
    assert scored_sha["comparison_reason"] == "producer_sha256_mismatch"
    assert scored_sha["key_matched"] == 0
    assert scored_sha["key_denominator"] == 2
    assert scored_sha["passed_10pct"] is False


def test_request_producer_sha_is_authoritative_without_a_cell_sha() -> None:
    foreign = "c" * 64
    both = {
        "status": "forecast",
        "cell": {"phase": "decode", "client_boundary": CLOCK, "producer_boundary": CLOCK},
        "requests": [
            _forecast_row(0, 112.0, sha=foreign),
            _forecast_row(1, 190.0, sha=foreign),
        ],
    }
    bound = _bind(both, witness=SHA)
    assert bound["prediction"]["producer_sha256"] == foreign
    assert bound["prediction"]["producer_sha256"] != SHA
    scored = _score(_interface(), bound["prediction"])
    assert scored["comparison_reason"] == "producer_sha256_mismatch"
    assert scored["key_matched"] == 0
    assert scored["key_denominator"] == 2
    assert scored["passed_10pct"] is False
    assert scored["per_key_errors"] == {}

    mixed = {
        "status": "forecast",
        "cell": {"phase": "decode", "client_boundary": CLOCK, "producer_boundary": CLOCK},
        "requests": [
            _forecast_row(0, 112.0, sha=foreign),
            _forecast_row(1, 190.0, sha=SHA),
        ],
    }
    conflicted = _bind(mixed, witness=SHA)
    assert conflicted["prediction"].get("producer_sha256") != SHA or not conflicted["prediction"].get("boundary_samples")
    assert conflicted["prediction"].get("producer_sha256", "") != SHA
    assert "boundary_samples" not in conflicted["prediction"]
    scored_mix = _score(_interface(), conflicted["prediction"])
    assert scored_mix["key_matched"] == 0
    assert scored_mix["comparison"] != "compared"
    assert scored_mix["passed_10pct"] is False
    assert scored_mix["per_key_errors"] == {}


def test_counterfactual_grade_is_not_paired_to_the_source() -> None:
    forecast = {
        "status": "forecast",
        "cell": {
            "phase": "decode",
            "client_boundary": CLOCK,
            "producer_sha256": SHA,
            "grade_eligible": False,
        },
        "requests": [
            {**_forecast_row(0, 50.0), "grade_eligible": False},
            {**_forecast_row(1, 70.0), "grade_eligible": False},
        ],
    }
    bound = _bind(forecast)
    assert "boundary_samples" not in bound["prediction"]
    scored = _score(_interface(), bound["prediction"])
    assert scored["key_matched"] == 0
    assert scored["key_denominator"] == 2
    assert scored["comparison"] != "compared"
    assert scored["passed_10pct"] is False


def test_duplicate_conflicting_time_is_not_a_silent_match() -> None:
    forecast = {
        "status": "forecast",
        "cell": {"phase": "decode", "client_boundary": CLOCK, "producer_sha256": SHA},
        "requests": [
            _forecast_row(0, 112.0),
            _forecast_row(1, 190.0),
            _forecast_row(0, 224.0),
        ],
    }
    bound = _bind(forecast)
    assert _key(0) not in bound["prediction"].get("boundary_samples", {})
    assert bound["prediction"]["boundary_samples"][_key(1)] == 190.0
    scored = _score(_interface(), bound["prediction"])
    assert scored["comparison"] != "compared"
    assert scored["comparison_reason"] == "sample_key_population_mismatch"
    assert _key(0) in scored["missing_keys"]
    assert _key(0) not in scored["per_key_errors"]
    assert scored["key_denominator"] == 2
    assert scored["key_matched"] == 1
    assert scored["passed_10pct"] is False
    assert scored["per_key_errors"][_key(1)] == pytest.approx(-0.05)


def test_typed_ttft_ms_scores_on_decode_and_itl_tpot_does_not() -> None:
    typed = _prediction({_key(0): 112.0, _key(1): 190.0})
    typed["boundary_samples"] = {_key(0): {"ttft_ms": 112.0}, _key(1): {"ttft_ms": 190.0}}
    typed["ttft_boundary"] = CLOCK
    typed["boundary_basis"] = "per_request_client_ttft"
    scored = _score(_interface(), typed)
    assert scored["comparison"] == "compared"
    assert scored["comparison_reason"] == "exact_keyed_samples"
    assert scored["per_key_errors"][_key(0)] == pytest.approx(0.12)
    assert scored["per_key_errors"][_key(1)] == pytest.approx(-0.05)
    assert scored["key_matched"] == 2

    itl = _prediction({_key(0): 100.0, _key(1): 200.0})
    itl["boundary_samples"] = {_key(0): {"tpot_ms": 100.0}, _key(1): {"tpot_ms": 200.0}}
    itl["boundary_basis"] = "per_request_inter_token_interval"
    itl["ttft_boundary"] = CLOCK
    rejected = _score(_interface(), itl)
    assert rejected["comparison"] != "compared"
    assert rejected["comparison_reason"] == "request_boundary_not_per_request"
    assert rejected["per_key_errors"] == {}
    assert rejected["key_matched"] == 0
    assert rejected["key_denominator"] == 2
    assert rejected["passed_10pct"] is False


def test_saved_forecasts_keep_the_three_real_cells_and_reject_the_controls() -> None:
    if not SAVED.is_file() or not CELLS.is_file():
        pytest.skip("saved ordinary forecasts are not in this workspace")
    import zero_shot_client_requests as client

    saved = json.loads(SAVED.read_text(encoding="utf-8"))
    forecasts = saved["forecasts_captured"]
    wanted = (
        "dsv41_dp16tp1ep16_dc_2k_c2",
        "dsv41_dp16tp1ep16_dc_2k_c4",
        "dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8",
    )
    rows = {}
    for line in CELLS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("cell_id") in wanted:
            rows[row["cell_id"]] = row
        if len(rows) == len(wanted):
            break
    assert set(rows) == set(wanted)
    scored_rows = []
    captures = {}
    for cell_id in wanted:
        capture = client.client_capture(rows[cell_id])
        captures[cell_id] = capture
        interface = client.p6_interface(capture)
        witness = str((capture.producer or {}).get("producer_sha256") or "")
        bound = benchmark._bind_request_forecast(
            cell_id,
            str(rows[cell_id].get("phase") or ""),
            capture.declarations,
            interface["requests"],
            witness,
            forecasts[cell_id],
        )
        assert bound["forecast_assumptions"]["host_overhead_status"] == "absent_assumed_zero"
        assert bound["forecast_assumptions"]["host_overhead_ms"] is None
        scored = gate.score_client_request_interface(interface, bound["prediction"], hardware_tier="A5")
        scored_rows.append(scored)
        assert scored["comparison"] == "compared"
        assert scored["producer_clock_status"] == "matched"
        assert scored["key_missing"] == 0
        assert bound["prediction"]["ttft_boundary"] == capture.producer.get("ttft_boundary")
        assert bound["prediction"]["producer_sha256"] == witness
    by_id = {row["capture_id"]: row for row in scored_rows}
    assert by_id["dsv41_dp16tp1ep16_dc_2k_c2"]["passed_10pct"] is True
    assert by_id["dsv41_dp16tp1ep16_dc_2k_c2"]["max_error"] == pytest.approx(0.0511664954882426)
    assert by_id["dsv41_dp16tp1ep16_dc_2k_c4"]["passed_10pct"] is False
    assert by_id["dsv41_dp16tp1ep16_dc_2k_c4"]["key_matched"] == 4
    assert by_id["dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8"]["key_matched"] == 8
    assert by_id["dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8"]["max_error"] == pytest.approx(0.711667763465051)
    assert sum(row["key_matched"] for row in scored_rows) == 14
    recorded = {item["capture_id"]: item for item in saved["ordinary_examples"]}
    assert recorded["dsv41_dp16tp1ep16_pf_128k_c1"]["key_matched"] == 1
    assert recorded["dsv41_dp16tp1ep16_pf_128k_c1"]["keys_over_10pct"] == 1

    mixed = "dsv41flash_dp16tp1ep16_2n_pd_32k_p4k_c8"
    other = captures["dsv41_dp16tp1ep16_dc_2k_c2"].producer
    interface = client.p6_interface(captures[mixed])
    witness = str(captures[mixed].producer.get("producer_sha256") or "")
    original = forecasts[mixed]

    swapped_clock = json.loads(json.dumps(original))
    swapped_clock["cell"]["client_boundary"] = other["ttft_boundary"]
    swapped_clock["cell"]["target_boundary"] = other["ttft_boundary"]
    clock_bound = benchmark._bind_request_forecast(
        mixed, "decode", captures[mixed].declarations, interface["requests"], witness, swapped_clock,
    )
    clock_score = gate.score_client_request_interface(interface, clock_bound["prediction"], hardware_tier="A5")
    assert clock_bound["prediction"].get("ttft_boundary") == other["ttft_boundary"]
    assert clock_score["key_matched"] == 0
    assert clock_score["comparison"] != "compared"

    swapped_sha = json.loads(json.dumps(original))
    swapped_sha["cell"]["producer_sha256"] = other["producer_sha256"]
    swapped_sha["cell"]["rack"] = other["rack"]
    sha_bound = benchmark._bind_request_forecast(
        mixed, "decode", captures[mixed].declarations, interface["requests"], witness, swapped_sha,
    )
    sha_score = gate.score_client_request_interface(interface, sha_bound["prediction"], hardware_tier="A5")
    assert sha_bound["prediction"]["producer_sha256"] == other["producer_sha256"]
    assert sha_score["comparison_reason"] == "producer_sha256_mismatch"
    assert sha_score["key_matched"] == 0

    duplicated = json.loads(json.dumps(original))
    duplicated["requests"].append({
        **duplicated["requests"][0],
        "predicted_ms": duplicated["requests"][0]["predicted_ms"] * 2,
    })
    dup_bound = benchmark._bind_request_forecast(
        mixed, "decode", captures[mixed].declarations, interface["requests"], witness, duplicated,
    )
    dup_score = gate.score_client_request_interface(interface, dup_bound["prediction"], hardware_tier="A5")
    assert dup_score["comparison_reason"] == "sample_key_population_mismatch"
    assert dup_score["key_matched"] == 7
    assert dup_score["key_denominator"] == 8
    assert duplicated["requests"][0]["key"] in dup_score["missing_keys"]

    typed_source = benchmark._bind_request_forecast(
        mixed, "decode", captures[mixed].declarations, interface["requests"], witness, original,
    )["prediction"]
    typed = dict(typed_source)
    typed["boundary_samples"] = {
        key: {"ttft_ms": value} for key, value in typed_source["boundary_samples"].items()
    }
    typed_score = gate.score_client_request_interface(interface, typed, hardware_tier="A5")
    assert typed_score["comparison_reason"] == "exact_keyed_samples"
    assert typed_score["key_matched"] == 8
    assert typed_score["max_error"] == pytest.approx(0.711667763465051)

    itl_samples = {}
    for request in interface["requests"]:
        itl_samples[request["key"]] = {"tpot_ms": request["observed_stream"]["itl_mean_s"] * 1000.0}
    itl = dict(typed_source)
    itl["boundary_samples"] = itl_samples
    itl["boundary_basis"] = "per_request_inter_token_interval"
    itl_score = gate.score_client_request_interface(interface, itl, hardware_tier="A5")
    assert itl_score["comparison_reason"] == "request_boundary_not_per_request"
    assert itl_score["key_matched"] == 0
    assert itl_score["per_key_errors"] == {}
    assert itl_score["passed_10pct"] is False
