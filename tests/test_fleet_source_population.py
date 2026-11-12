"""Scope and denominator regression for the fleet gate.

The gate must keep the measured observation when a prediction is missing,
partial, wrong, or invalid. Counts come from ``hf_sample_scoring``. This file
does not refit timings and does not rewrite source rows.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import fleet_capture_observations as observations  # noqa: E402
import fleet_operator_modeling as modeling  # noqa: E402
import hf_benchmark_gate as gate  # noqa: E402
import hf_profiling_benchmark as benchmark  # noqa: E402
import hf_sample_scoring as scoring  # noqa: E402

FLEET = Path("/tmp/mindie-sim-profiling-bench/data/fleet_captures.jsonl")
ZERO_SHOT = Path("/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl")
BODY_IDS = (
    "registered_decode:glm53flash-a3-tp16-c4-livepre",
    "dsh_heldout:a3/heldout_engine_20261030/kimi_k3_w4a8_4layer_tp16_ep16_heldout_20261030/prof/prefill_c1_p16k/kernel_details.csv",
    "wave5:a2:a2/a2_real_dsv2lite_E64_K6_tp4ep4_prefill:a2_real_dsv2lite_E64_K6_tp4ep4_prefill_4k_c1",
    "wave5:a5:a5/a5_qwen30ba3b_tp4_ep4_decode:a5_qwen30ba3b_tp4_ep4_decode_4k_c1",
)


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def _forward_observation(keys: list[str]) -> dict:
    return {
        "capture": {"capture_id": "ex", "phase": "decode", "hardware_tier": "A5"},
        "source": {"sha256": "ab", "path": "/obs/kernel_details.csv"},
        "measurements": {"per_forward_window": {
            "status": "measured",
            "samples_basis": "elapsed",
            "samples": [
                {"key": key, "observed_ms": 10.0, "phase": "decode", "forward_id": key}
                for key in keys
            ],
        }},
    }


def _request_observation() -> dict:
    return {
        "capture": {"capture_id": "ex", "phase": "prefill", "hardware_tier": "A5"},
        "source": {"sha256": "ab", "path": "/obs/client.json"},
        "measurements": {"native_client_request": {
            "status": "measured",
            "phase": "prefill",
            "samples_basis": "elapsed",
            "samples": [{"key": "request:0", "observed_ms": 5.0, "phase": "prefill"}],
        }},
    }


def _calls_observation() -> dict:
    return {
        "capture": {"capture_id": "ex", "phase": "decode", "hardware_tier": "A5"},
        "source": {},
        "measurements": {"native_calls": {
            "status": "measured",
            "native_phase": "prefill",
            "source_sha256": "ab",
            "samples_basis": "elapsed_native_call_span_ms",
            "samples": [
                {"key": "call0", "observed_ms": 1.0, "phase": "prefill"},
                {"key": "call1", "observed_ms": 1.0, "phase": "prefill"},
            ],
        }},
    }


def _prediction(boundary: str, keys: list[str], *, status: str = "modeled", sha: str = "ab") -> dict:
    return {
        "status": status,
        "prediction_boundary": boundary,
        "boundary_basis": "elapsed",
        "capture_id": "ex",
        "phase": "decode",
        "hardware_tier": "A5",
        "source_sha256": sha,
        "boundary_samples": [
            {"key": key, "boundary_ms": 10.0, "phase": "decode", "forward_id": key}
            for key in keys
        ],
    }


def _row() -> dict:
    return {"capture_id": "ex", "suite": "unit", "phase": "decode", "hardware_tier": "A5"}


def _load_fleet(wanted: set[str] | None = None) -> list[dict]:
    if not FLEET.is_file():
        pytest.skip(f"fleet table absent: {FLEET}")
    rows = []
    with FLEET.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if wanted is None or row.get("capture_id") in wanted:
                rows.append(row)
    return rows


def test_missing_partial_wrong_and_unknown_scopes_stay_honest() -> None:
    """Independent counterexample. Prediction scope cannot rewrite the observation."""
    keys = ["f0", "f1", "f2"]
    observation = _forward_observation(keys)
    row = _row()

    missing = gate.score_fleet_row(row, observation, {})
    assert missing["boundary_scope"] == "forward_body"
    assert missing["population_boundary"] == "per_forward_window"
    assert missing["comparison"] == "uncovered"
    assert missing["key_denominator"] == 3
    assert missing["key_matched"] == 0
    assert missing["key_missing"] == 3
    assert missing["passed_10pct"] is False

    partial = gate.score_fleet_row(row, observation, _prediction("per_forward_window", ["f0"]))
    assert partial["boundary_scope"] == "forward_body"
    assert partial["comparison"] == "invalid"
    assert partial["comparison_reason"] == "sample_key_population_mismatch"
    assert partial["key_denominator"] == 3
    assert partial["key_matched"] == 1
    assert partial["key_missing"] == 2
    assert partial["group_passed_10pct"] is False

    wrong = gate.score_fleet_row(
        row, observation,
        {"status": "modeled", "prediction_boundary": "native_client_request",
         "boundary_basis": "elapsed", "capture_id": "ex", "phase": "decode", "hardware_tier": "A5",
         "boundary_samples": [{"key": "request:0", "boundary_ms": 10.0, "phase": "decode"}]},
    )
    assert wrong["boundary_scope"] == "forward_body"
    assert wrong["comparison_reason"] == "prediction_boundary_scope_mismatch"
    assert wrong["key_denominator"] == 3
    assert wrong["key_matched"] == 0
    assert wrong["key_missing"] == 3

    invented = gate.score_fleet_row(
        row, observation, _prediction("per_forward_totally_different_latencies", keys))
    assert invented["boundary_scope"] == "forward_body"
    assert invented["comparison"] != "compared"
    assert invented["key_denominator"] == 3
    assert invented["key_matched"] == 0
    assert invented["key_missing"] == 3
    assert invented["prediction_boundary"] == "per_forward_totally_different_latencies"

    invalid = gate.score_fleet_row(
        row, observation, _prediction("per_forward_window", keys, sha="cd"))
    assert invalid["boundary_scope"] == "forward_body"
    assert invalid["comparison"] == "invalid"
    assert invalid["key_denominator"] == 3
    assert invalid["key_matched"] == 0

    request = gate.score_fleet_row(
        row, _request_observation(), _prediction("per_forward_window", ["f0"]))
    assert request["boundary_scope"] == "request_l4"
    assert request["population_boundary"] == "native_client_request"
    assert request["key_denominator"] == 1
    assert request["key_missing"] == 1
    assert request["key_matched"] == 0

    calls = gate.score_fleet_row(
        {"capture_id": "ex", "suite": "operator_and_kernel_calibration_20261107",
         "phase": "decode", "hardware_tier": "A5"},
        _calls_observation(), {})
    assert calls["boundary_scope"] == "standalone"
    assert calls["comparison"] == "not_a_body_step"
    assert calls["key_denominator"] == 2
    assert calls["key_missing"] == 2
    assert calls["key_matched"] == 0

    unknown = gate.score_fleet_row(row, {"measurements": {}, "source": {}}, {})
    assert unknown["boundary_scope"] == "unknown"
    assert unknown["key_denominator"] is None
    assert unknown["key_missing"] is None
    assert unknown["boundary_scope"] != "forward_body"


def test_registered_source_relations_keep_in_sample_and_not_blind_groups() -> None:
    """72 in_sample and 91 not_blind stay inside the 306 registered source rows."""
    if not (benchmark.RESULTS_DIR / "decode.json").is_file():
        pytest.skip("structure results are not in this checkout")
    rows = benchmark._collect_structure_suites()[0]
    report = gate._identity_report([], rows)
    assert report["retained_source_relations"] == 306
    assert report["in_sample_group"] == 72
    assert report["not_blind_group"] == 91
    assert report["decode_in_sample"] == 68
    assert report["prefill_in_sample"] == 1
    assert report["not_blind"] == 77
    glm = report["by_id_role"]["registered_decode:glm53flash-a3-tp16-c4-livepre"]
    disclosed = {"evaluation_relation": "zero_shot", "calibration_role": "zero_shot", "coverage_only": False}
    gate._apply_source_role(disclosed, glm)
    assert disclosed["evaluation_relation"] == "in_sample"
    assert disclosed["coverage_only"] is True
    assert "zero_shot" not in str(disclosed["evaluation_relation"])


def test_four_real_body_rows_keep_216_keys() -> None:
    """216 source keys. A paired key uses |model-original|/|original| and the unchanged 10% group rule."""
    rows = _load_fleet(set(BODY_IDS))
    by_id = {row["capture_id"]: row for row in rows}
    assert set(by_id) == set(BODY_IDS)
    packed = []
    for capture_id in BODY_IDS:
        row = by_id[capture_id]
        cfg = gate.prediction_config(row)
        observation = observations.extract_capture_observations(cfg)
        prediction = modeling.predict_capture_operators_and_step(cfg)
        packed.append((observation, prediction, gate.score_fleet_row(row, observation, prediction)))
    scored = [item for _observation, _prediction, item in packed]
    assert [item["boundary_scope"] for item in scored] == ["forward_body"] * 4
    assert sum(item["key_denominator"] for item in scored) == 216
    qwen = next(item for item in scored if "qwen30ba3b" in item["capture_id"])
    assert qwen["key_denominator"] == 139 and qwen["comparison"] == "compared"
    assert qwen["evaluation_relation"] == "regime_table_replay"
    assert qwen["calibration_role"] == "regime_table_replay"
    assert qwen["coverage_only"] is True and qwen["target_timing_used_to_fit"] is True
    assert qwen["model_target_timing_used_to_fit"] is False
    assert qwen["slice_role_inherited"] is False
    assert len(qwen["per_key_errors"]) == 139
    for observation, prediction, item in packed:
        population = scoring.observed_boundary_population(observation, item["prediction_boundary"])
        assert population["status"] == "measured"
        assert item["key_denominator"] == population["denominator"] == len(population["keys"])
        if item["comparison"] != "compared":
            assert item["group_passed_10pct"] is False
            assert item["key_matched"] == 0
            assert item["key_missing"] == item["key_denominator"]
            continue
        predicted = {row["key"]: row["boundary_ms"] for row in prediction["boundary_samples"]}
        over = 0
        for key, observed in zip(population["keys"], population["values"]):
            value = predicted[key]
            signed = (float(value) - float(observed)) / abs(float(observed))
            assert item["per_key_errors"][key] == pytest.approx(signed)
            if abs(signed) > 0.10:
                over += 1
        assert item["key_matched"] == len(population["keys"])
        assert item["key_missing"] == 0
        assert item["keys_over_10pct"] == over
        assert item["group_passed_10pct"] is (over == 0)
    glm = next(item for item in scored if item["capture_id"].startswith("registered_decode:"))
    report = gate._identity_report([], benchmark._collect_structure_suites()[0])
    gate._apply_source_role(glm, report["by_id_role"][glm["capture_id"]])
    assert glm["evaluation_relation"] == "in_sample"
    assert glm["coverage_only"] is True
    kimi = next(item for item in scored if "kimi_k3" in item["capture_id"])
    invented = modeling.predict_capture_operators_and_step(gate.prediction_config(by_id[kimi["capture_id"]]))
    invented = dict(invented)
    invented["prediction_boundary"] = "per_forward_window_time_inside_allocator_wait"
    held = gate.score_fleet_row(
        by_id[kimi["capture_id"]],
        observations.extract_capture_observations(gate.prediction_config(by_id[kimi["capture_id"]])),
        invented,
    )
    assert held["boundary_scope"] == "forward_body"
    assert held["comparison"] != "compared"
    assert held["key_denominator"] == 3
    assert held["key_matched"] == 0
    assert held["key_missing"] == 3


def test_dsh_wave5_2228_absent_prediction_keeps_forward_windows() -> None:
    """2,228 original IDs. Withheld prediction must not drop the 195,238 windows."""
    if not FLEET.is_file():
        pytest.skip(f"fleet table absent: {FLEET}")
    denominator = missing = rows_n = 0
    with FLEET.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            capture_id = str(row.get("capture_id") or "")
            if not (capture_id.startswith("dsh_heldout:") or capture_id.startswith("wave5:")):
                continue
            observation = observations.extract_capture_observations(gate.prediction_config(row))
            scored = gate.score_fleet_row(row, observation, {})
            population = scoring.observed_boundary_population(observation)
            assert scored["boundary_scope"] == "forward_body"
            assert scored["population_boundary"] == "per_forward_window"
            assert scored["comparison"] != "compared"
            assert scored["key_denominator"] == population["denominator"]
            assert scored["key_denominator"] == scored["key_missing"]
            assert scored["key_matched"] == 0
            denominator += int(scored["key_denominator"])
            missing += int(scored["key_missing"])
            rows_n += 1
    assert rows_n == 2228
    assert denominator == 195238
    assert missing == 195238


def test_29_calls_do_not_zero_a_measured_population() -> None:
    """Independent calls keep their own denominator. test6's 3 measurements stay missing."""
    if not FLEET.is_file():
        pytest.skip(f"fleet table absent: {FLEET}")
    seen = 0
    test6 = None
    with FLEET.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("suite") != "operator_and_kernel_calibration_20261107":
                continue
            seen += 1
            cfg = gate.prediction_config(row)
            observation = observations.extract_capture_observations(cfg)
            population = scoring.observed_boundary_population(observation)
            withheld = gate.score_fleet_row(row, observation, {})
            predicted = gate.score_fleet_row(row, observation, modeling.predict_capture_operators_and_step(cfg))
            if population.get("status") == "measured":
                expected = {
                    "native_calls": "standalone",
                    "per_forward_window": "forward_body",
                    "native_client_request": "request_l4",
                }[population["boundary"]]
                assert withheld["boundary_scope"] == expected
                assert withheld["key_denominator"] == population["denominator"]
                assert withheld["key_missing"] == population["denominator"]
                assert withheld["key_matched"] == 0
                assert predicted["key_denominator"] == population["denominator"]
                assert predicted["boundary_scope"] == expected
            else:
                assert withheld["boundary_scope"] == "unknown"
                assert withheld["key_denominator"] is None
                assert withheld["key_missing"] is None
            if "test6_e16k4_q64" in str(row.get("capture_id")):
                test6 = withheld
    assert seen == 29
    assert test6 is not None
    assert test6["boundary_scope"] == "standalone"
    assert test6["key_denominator"] == 3
    assert test6["key_missing"] == 3
    assert test6["key_matched"] == 0


def test_94_client_singletons_stay_request_scope_without_a_timing_fit() -> None:
    """Producer singleton eligibility only. No L4 timing prediction is run."""
    if not ZERO_SHOT.is_file():
        pytest.skip(f"zero-shot table absent: {ZERO_SHOT}")
    import zero_shot_actual_entry as entry

    paths = entry._index(entry.DEFAULT_ROOTS)
    eligible = 0
    with ZERO_SHOT.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            cell_id = str(row.get("cell_id") or "")
            phase = str(row.get("phase") or "")
            path = paths.get(cell_id.split(":")[-1])
            if path is None:
                continue
            try:
                raw = json.loads(Path(path).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            decision = gate.singleton_request_ttft(raw if isinstance(raw, dict) else {}, phase)
            if not decision.get("eligible"):
                continue
            eligible += 1
            observation = {
                "capture": {"capture_id": cell_id, "phase": phase, "hardware_tier": str(row.get("hardware_tier") or "")},
                "source": {"independent": True, "path": str(path)},
                "measurements": {"native_client_request": {
                    "status": "measured",
                    "phase": phase,
                    "samples_basis": "singleton_request_ttft_ms",
                    "samples": [{
                        "key": decision.get("key") or "request:0",
                        "observed_ms": decision["observed_ms"],
                        "phase": phase,
                    }],
                }},
            }
            fleet_row = {"capture_id": cell_id, "suite": "zero_shot", "phase": phase}
            withheld = gate.score_fleet_row(fleet_row, observation, {})
            assert withheld["boundary_scope"] == "request_l4"
            assert withheld["population_boundary"] == "native_client_request"
            assert withheld["key_denominator"] == 1
            assert withheld["key_missing"] == 1
            assert withheld["key_matched"] == 0
            wrong = gate.score_fleet_row(fleet_row, observation, {
                "status": "modeled",
                "prediction_boundary": "per_forward_window",
                "boundary_basis": "elapsed",
                "capture_id": cell_id,
                "phase": phase,
            })
            assert wrong["boundary_scope"] == "request_l4"
            assert wrong["key_denominator"] == 1
            assert wrong["key_missing"] == 1
            assert wrong["comparison"] != "compared"
    assert eligible == 94


def _slice_observation(phase: str, raw_sha: str, frames: list[dict], receipt: str = "/receipts/same.json") -> dict:
    return {
        "measurements": {"per_forward_window": {
            "status": "measured",
            "raw_digest_verified": True,
            "raw_sha256": raw_sha,
            "source_sha256": raw_sha,
            "raw_path": "/kernels/same/kernel_details.csv",
            "window_source": receipt,
            "boundary": "per_forward_window_source_receipt",
            "frame_identifiers": frames,
        }},
    }


def _frame(phase: str, forward_id: str, start: int) -> dict:
    return {
        "phase": phase, "rank_id": "0", "device_id": "0", "forward_id": forward_id,
        "start_ns": start, "end_ns": start + 1000,
    }


def test_slice_role_follows_verified_windows_not_a_recomputed_label() -> None:
    """Same kernel, receipt, and key windows inherit the earliest calibration.

    A different phase is not that slice. A later actual relation is not overwritten.
    Duration and capture id are not the join.
    """
    raw = "ab" * 32
    frames = [_frame("decode", "f0", 10), _frame("decode", "f1", 20)]
    other_phase = [_frame("prefill", "f0", 10), _frame("prefill", "f1", 20)]
    donor = {
        "capture_id": "wave5:donor", "suite": "wave5_20261031", "duration_ms": 1,
        "source_calibration": {
            "evaluation_relation": "regime_table_replay",
            "target_timing_used_to_fit": True,
            "calibration_role": "regime_table_replay",
        },
        "calibration_role": "regime_table_replay",
        "target_timing_used_to_fit": True,
    }
    extended = {
        "capture_id": "extended:alias", "suite": "extended_a3_a5_workstream_captures", "duration_ms": 999,
        "source_calibration": {
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False,
        },
    }
    other = {
        "capture_id": "extended:other-phase", "suite": "extended_a3_a5_workstream_captures",
        "source_calibration": {
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False,
        },
    }
    rows = [donor, extended, other]
    observations = [
        _slice_observation("decode", raw, frames),
        _slice_observation("decode", raw, frames, receipt="/receipts/other-file.json"),
        _slice_observation("prefill", raw, other_phase),
    ]
    report = gate.disclose_source_slices(
        [gate.slice_record(row, observation) for row, observation in zip(rows, observations)],
        rows,
    )
    cohort = report["cohort"]
    assert cohort["population_rows"] == 3
    assert cohort["measured_ids"] == 3
    assert cohort["id_window_rows"] == 6
    assert cohort["unique_physical_series"] == 2
    assert cohort["unique_physical_windows"] == 4
    assert cohort["alias_groups"] == 1
    assert report["alias_groups"][0]["conflict"] is False
    extended_info = report["by_id"]["extended:alias"]
    assert extended_info["inherited"] is True
    assert extended_info["donor_capture_id"] == "wave5:donor"
    assert extended_info["evaluation_relation"] == "regime_table_replay"
    assert extended_info["target_timing_used_to_fit"] is True
    labeled = {
        "capture_id": "extended:alias",
        "evaluation_relation": "zero_shot_piecewise_recomputed",
        "calibration_role": "zero_shot_piecewise_recomputed",
        "coverage_only": False,
        "target_timing_used_to_fit": False,
    }
    gate.apply_slice_disclosure(labeled, extended_info)
    assert labeled["capture_id"] == "extended:alias"
    assert labeled["evaluation_relation"] == "regime_table_replay"
    assert labeled["coverage_only"] is True
    assert labeled["target_timing_used_to_fit"] is True
    assert labeled["slice_role_inherited"] is True
    assert "zero_shot_piecewise_recomputed" not in labeled["evaluation_relation"]
    phase_info = report["by_id"]["extended:other-phase"]
    assert phase_info["inherited"] is False
    assert phase_info["evaluation_relation"] is None
    held = {
        "capture_id": "extended:other-phase",
        "evaluation_relation": "zero_shot_piecewise_recomputed",
        "coverage_only": False,
    }
    gate.apply_slice_disclosure(held, phase_info)
    assert held["evaluation_relation"] == "zero_shot_piecewise_recomputed"
    assert held["coverage_only"] is False
    conflict_donor = dict(donor)
    conflict_donor["capture_id"] = "wave5:donor"
    conflict_other = {
        "capture_id": "registered:other", "suite": "registered_decode",
        "source_calibration": {
            "evaluation_relation": "in_sample",
            "target_timing_used_to_fit": True,
            "calibration_role": "in_sample",
        },
        "calibration_role": "in_sample",
        "target_timing_used_to_fit": True,
    }
    conflict_alias = dict(extended)
    conflict_alias["capture_id"] = "extended:disputed"
    conflict_rows = [conflict_donor, conflict_other, conflict_alias]
    conflict_report = gate.disclose_source_slices(
        [gate.slice_record(row, _slice_observation("decode", raw, frames)) for row in conflict_rows],
        conflict_rows,
    )
    assert conflict_report["alias_groups"][0]["conflict"] is True
    conflicted = {
        "capture_id": "registered:other",
        "evaluation_relation": "in_sample",
        "calibration_role": "in_sample",
        "coverage_only": True,
        "target_timing_used_to_fit": True,
    }
    gate.apply_slice_disclosure(conflicted, conflict_report["by_id"]["registered:other"])
    assert conflicted["evaluation_relation"] == "in_sample"
    assert conflicted.get("slice_role_inherited") is not True
    disputed = {
        "capture_id": "extended:disputed",
        "evaluation_relation": "zero_shot_piecewise_recomputed",
        "coverage_only": False,
    }
    gate.apply_slice_disclosure(disputed, conflict_report["by_id"]["extended:disputed"])
    assert disputed["evaluation_relation"] == "zero_shot_piecewise_recomputed"
    assert disputed["coverage_only"] is False


def test_shared_source_slices_keep_wave5_relation_and_full_denominators() -> None:
    """780 Wave5 aliases stay regime_table_replay. 2228/195238 and 3304/302422 stay."""
    if not FLEET.is_file():
        pytest.skip(f"fleet table absent: {FLEET}")
    if not (benchmark.RESULTS_DIR / "wave5_full_generalization.json").is_file():
        pytest.skip("wave5 source results are not in this checkout")
    fleet_rows = []
    with FLEET.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                fleet_rows.append(json.loads(line))
    ids = [str(row.get("capture_id") or "") for row in fleet_rows]
    assert len(ids) == len(set(ids)) == 6606
    calibration_rows = benchmark._collect_structure_suites()[0]
    wave5_ids = [row["capture_id"] for row in fleet_rows if str(row.get("capture_id") or "").startswith("wave5:")]
    calibration_by_id = {str(row.get("capture_id") or ""): row for row in calibration_rows}
    assert len(wave5_ids) == 1653
    assert all(
        (calibration_by_id[cid].get("source_calibration") or {}).get("evaluation_relation") == "regime_table_replay"
        and calibration_by_id[cid].get("target_timing_used_to_fit") is True
        for cid in wave5_ids
    )
    records = []
    denominator = missing = rows_n = 0
    body_denominators = {}
    for row in fleet_rows:
        observation = observations.extract_capture_observations(gate.prediction_config(row))
        records.append(gate.slice_record(row, observation))
        capture_id = str(row.get("capture_id") or "")
        if capture_id.startswith("dsh_heldout:") or capture_id.startswith("wave5:"):
            scored = gate.score_fleet_row(row, observation, {})
            population = scoring.observed_boundary_population(observation)
            assert scored["boundary_scope"] == "forward_body"
            assert scored["population_boundary"] == "per_forward_window"
            assert scored["comparison"] != "compared"
            assert scored["key_denominator"] == population["denominator"] == scored["key_missing"]
            assert scored["key_matched"] == 0
            denominator += int(scored["key_denominator"])
            missing += int(scored["key_missing"])
            rows_n += 1
        if capture_id in BODY_IDS:
            body_denominators[capture_id] = scoring.observed_boundary_population(observation)["denominator"]
    assert rows_n == 2228
    assert denominator == missing == 195238
    assert sum(body_denominators[cid] for cid in BODY_IDS) == 216
    report = gate.disclose_source_slices(records, calibration_rows)
    cohort = report["cohort"]
    assert cohort["population_rows"] == 6606
    assert cohort["measured_ids"] == 3304
    assert cohort["id_window_rows"] == 302422
    assert cohort["unique_physical_series"] == 2523
    assert cohort["unique_physical_windows"] == 219918
    assert cohort["measured_ids"] != cohort["unique_physical_series"]
    assert cohort["id_window_rows"] - cohort["unique_physical_windows"] == cohort["repeated_id_window_rows"]
    wave5_extended = []
    registered_extended = []
    for group in report["alias_groups"]:
        suites = set(group["suites"])
        assert group["conflict"] is False
        assert len(group["capture_ids"]) == 2
        assert len({report["by_id"][cid]["scope_phase"] for cid in group["capture_ids"]}) == 1
        if suites == {"wave5_20261031", "extended_a3_a5_workstream_captures"}:
            wave5_extended.append(group)
        elif "extended_a3_a5_workstream_captures" in suites and any(suite.startswith("registered_") for suite in suites):
            registered_extended.append(group)
    assert len(wave5_extended) == 780
    assert len(registered_extended) == 1
    assert len(report["alias_groups"]) == 781
    for group in wave5_extended:
        assert group["evaluation_relation"] == "regime_table_replay"
        assert group["target_timing_used_to_fit"] is True
        for capture_id, suite in zip(group["capture_ids"], group["suites"]):
            info = report["by_id"][capture_id]
            labeled = {
                "capture_id": capture_id,
                "evaluation_relation": "zero_shot_piecewise_recomputed",
                "calibration_role": "zero_shot_piecewise_recomputed",
                "coverage_only": False,
                "target_timing_used_to_fit": False,
            }
            gate.apply_slice_disclosure(labeled, info)
            assert labeled["capture_id"] == capture_id
            assert labeled["evaluation_relation"] == "regime_table_replay"
            assert labeled["target_timing_used_to_fit"] is True
            assert labeled["coverage_only"] is True
            assert "zero_shot_piecewise_recomputed" not in labeled["evaluation_relation"]
            if suite == "extended_a3_a5_workstream_captures":
                assert info["inherited"] is True
                assert labeled["slice_role_inherited"] is True
                assert str(info["donor_capture_id"]).startswith("wave5:")
            else:
                assert info["inherited"] is False
    group = registered_extended[0]
    donor_id = group["donor_capture_id"]
    donor_relation = group["evaluation_relation"]
    assert donor_relation and donor_relation != "zero_shot_piecewise_recomputed"
    for capture_id, suite in zip(group["capture_ids"], group["suites"]):
        assert capture_id in ids
        if suite != "extended_a3_a5_workstream_captures":
            continue
        labeled = {
            "capture_id": capture_id,
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "coverage_only": False,
            "target_timing_used_to_fit": False,
        }
        gate.apply_slice_disclosure(labeled, report["by_id"][capture_id])
        assert labeled["evaluation_relation"] == donor_relation
        assert labeled["slice_role_source_id"] == donor_id
        assert labeled["slice_role_inherited"] is True
        assert "zero_shot_piecewise_recomputed" not in labeled["evaluation_relation"]


def test_three_original_request_scopes_keep_separate_ttft_keys() -> None:
    """Prefill C1, one mixed run, and one C>1 cell with a rounded TTFT collision.

    The singleton helper stays prefill-only. Decode first-token TTFT is still a
    request key. A scalar model is not repeated across concurrent keys.
    """
    if not ZERO_SHOT.is_file():
        pytest.skip(f"zero-shot table absent: {ZERO_SHOT}")
    import zero_shot_client_requests as client

    rows = [json.loads(line) for line in ZERO_SHOT.open(encoding="utf-8") if line.strip()]
    chosen: dict[str, tuple] = {}
    for capture in client.iter_client_captures(rows):
        interface = client.p6_interface(capture)
        cell = interface["cell"]
        phase = str(cell.get("phase") or "")
        concurrency = int(cell.get("concurrency") or 0)
        requests = [item for item in interface["requests"] if isinstance(item, dict)]
        rounded: dict[float, str] = {}
        duplicate = False
        for request in requests:
            try:
                token = round(float(request["ttft_s"]), 6)
            except (TypeError, ValueError):
                continue
            previous = rounded.get(token)
            if previous is not None and previous != request["key"]:
                duplicate = True
            rounded[token] = str(request["key"])
        if "prefix" not in chosen and phase == "prefill" and concurrency == 1 and len(requests) == 1:
            chosen["prefix"] = (capture, interface)
        if "mixed" not in chosen and cell.get("mixed_prompt"):
            chosen["mixed"] = (capture, interface)
        if "multi" not in chosen and concurrency > 1 and duplicate:
            chosen["multi"] = (capture, interface)
        if "decode_c1" not in chosen and phase == "decode" and concurrency == 1 and len(requests) == 1:
            chosen["decode_c1"] = (capture, interface)
        if len(chosen) == 4:
            break
    assert set(chosen) == {"prefix", "mixed", "multi", "decode_c1"}

    prefix_capture, prefix_interface = chosen["prefix"]
    raw = json.loads(Path(prefix_capture.measured_path).read_text(encoding="utf-8"))
    assert gate.singleton_request_ttft(raw, "prefill")["eligible"] is True
    prefix = gate.score_client_request_interface(prefix_interface, {})
    assert prefix["boundary_scope"] == "request_l4"
    assert prefix["key_denominator"] == prefix["key_missing"] == 1
    assert prefix["key_matched"] == 0
    assert prefix["comparison"] != "compared"
    assert prefix["request_ttft_boundaries"]
    assert prefix["tpot_domain"] == "not_scored_on_request_ttft"

    decode_capture, decode_interface = chosen["decode_c1"]
    decode_raw = json.loads(Path(decode_capture.measured_path).read_text(encoding="utf-8"))
    decode_decision = gate.singleton_request_ttft(decode_raw, "decode")
    assert decode_decision["eligible"] is False
    assert decode_decision["reason"] == "tpot_not_a_per_step_boundary"
    decode = gate.score_client_request_interface(decode_interface, {})
    assert decode["boundary_scope"] == "request_l4"
    assert decode["key_denominator"] == decode["key_missing"] == 1
    assert decode["key_matched"] == 0

    for name in ("mixed", "multi"):
        _capture, interface = chosen[name]
        scored = gate.score_client_request_interface(interface, {})
        count = len(interface["requests"])
        assert count > 1
        assert scored["boundary_scope"] == "request_l4"
        assert scored["key_denominator"] == scored["key_missing"] == count
        assert scored["key_matched"] == 0
        assert scored["comparison"] != "compared"
        assert scored["request_ttft_boundaries"]
        declaration = client.prediction_declaration(_capture)
        text = json.dumps(declaration)
        assert "ttft_s" not in text
        assert "e2e_s" not in text

    _multi_capture, multi_interface = chosen["multi"]
    collided: dict[float, list[str]] = {}
    for request in multi_interface["requests"]:
        collided.setdefault(round(float(request["ttft_s"]), 6), []).append(str(request["key"]))
    groups = [keys for keys in collided.values() if len(keys) > 1]
    assert groups
    withheld = gate.score_client_request_interface(multi_interface, {})
    missing = set(withheld["missing_keys"])
    for keys in groups:
        assert len(keys) == len(set(keys))
        assert set(keys) <= missing
    scalar = gate.score_client_request_interface(multi_interface, {
        "status": "modeled",
        "prediction_boundary": "native_client_request",
        "boundary_ms": 10.0,
    })
    assert scalar["request_scalar_withheld"] is True
    assert scalar["key_denominator"] == scalar["key_missing"] == len(multi_interface["requests"])
    assert scalar["key_matched"] == 0
    assert scalar["comparison"] != "compared"
    held = gate.score_l4_bundle(
        {"cell_id": multi_interface["cell"]["cell_id"], "phase": "decode"},
        {"eligible": False, "reason": "request_population_not_singleton", "interface": multi_interface, "streams": 16},
        tier="A5",
    )
    assert held["capture_id"] == multi_interface["cell"]["cell_id"]
    assert held["comparison_reason"] != "request_population_not_singleton"
    assert held["comparison_reason"] != "tpot_not_a_per_step_boundary"
    assert held["key_missing"] == len(multi_interface["requests"])
    assert len(held["missing_keys"]) == len(multi_interface["requests"])
    assert held["l4_eligible"] is False


def test_unobserved_ordinal_stays_distinct_from_a_missing_ttft() -> None:
    """A declared ordinal with no row is unobserved. A row without TTFT is missing."""
    interface = {
        "cell": {"cell_id": "cell-a", "phase": "prefill", "rack": "rack06", "missing_ordinals": [1]},
        "requests": [
            {"key": "cell-a|ordinal=0", "launch_ordinal": 0, "ttft_s": 0.2, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
            {"key": "cell-a|ordinal=2", "launch_ordinal": 2, "ttft_s": None, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
        ],
        "declarations": [
            {"key": "cell-a|ordinal=0", "ordinal": 0, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
            {"key": "cell-a|ordinal=1", "ordinal": 1, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
            {"key": "cell-a|ordinal=2", "ordinal": 2, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
        ],
    }
    scored = gate.score_client_request_interface(interface, {})
    assert scored["capture_id"] == "cell-a"
    assert scored["key_denominator"] == 3
    assert scored["key_missing"] == 3
    assert set(scored["missing_keys"]) == {"cell-a|ordinal=0", "cell-a|ordinal=1", "cell-a|ordinal=2"}
    assert scored["request_ttft_absent"] == 1
    assert scored["request_ttft_unobserved"] == 1
    assert scored["request_ttft_orphans"] == 0
    assert scored["producer_rack"] == "rack06"
    assert scored["hardware_tier"] == ""
    assert scored["tpot_domain"] == "not_scored_on_request_ttft"
