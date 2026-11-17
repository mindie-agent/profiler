"""T16 real native cohort: ABI/call/window export and independent comparison.

The retained r64 QBMM pair is one actual full-grid call and one tail call from
the same A5 capture.  The predictor used in the real-data test is the existing
mindie-sim measured dual-load service path; it consumes a timing-free request
and never reads the observed duration.  A failing full-grid item is retained as
a finding, not averaged away.
"""
from copy import deepcopy
import builtins
import csv
import json
import os
from pathlib import Path
import shutil

import pytest

from mindie_profiler.compare_acceptance import (
    NATIVE_COMPARISON_SCHEMA,
    compare_native_predictions,
    main,
)
from mindie_profiler.native_tensor_abi import native_abi_from_slots
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.sim_bridge import (
    NATIVE_OBSERVATION_SCHEMA,
    NATIVE_REQUEST_SCHEMA,
    export_native_observations,
    native_prediction_requests,
    predict_native_requests,
)

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "tests" / "fixtures" / "r64_qbmm_dual_load" / "kernel_details.csv"
PROVENANCE = ROOT / "tests" / "fixtures" / "r64_qbmm_dual_load" / "provenance.json"
CONDITIONS = {
    "hardware": "Ascend950DT_9582", "phase": "prefill",
    "model": "glm-5.1", "quant": "W8A8_MXFP8",
}


@pytest.fixture(scope="module")
def exported():
    return export_native_observations(
        CAPTURE, include_hash=True, **CONDITIONS)


@pytest.fixture(scope="module")
def requests(exported):
    return native_prediction_requests(exported)


def _capture_variant(tmp_path, changes, name="kernel_details.csv"):
    with CAPTURE.open(newline="") as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames
        base = next(reader)
    path = tmp_path / name
    with path.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for values in changes:
            row = dict(base)
            row.update(values)
            writer.writerow(row)
    return path


def _sim_supply():
    pytest.importorskip("mindie_sim")
    import mindie_sim
    rel = Path("tests/fixtures/r64_qbmm_dual_load/supply.json")
    supply = Path(mindie_sim.__file__).resolve().parent.parent / rel
    if not supply.is_file():
        sibling = Path(__file__).resolve().parents[2] / "sim" / rel
        if sibling.is_file():
            supply = sibling
    if not supply.is_file():
        pytest.skip(f"sim dual-load supply unavailable: {supply}")
    return supply


def _qbmm_abi_from_op(op):
    """Build the full r64 MXFP8 QBMM ABI from the selected sim operator only."""
    metadata = dict(op.metadata)
    if (op.family != "gemm" or op.recipe != "output"
            or metadata.get("weight_representation") != "fp8_block1x32_fp8_e8m0"
            or metadata.get("activation_group_size") != 32
            or metadata.get("activation_scale_format") != "fp8_e8m0"
            or metadata.get("weight_format") != "fp8_e4m3"
            or metadata.get("activation_format") != "fp8_e4m3"
            or metadata.get("output_format") != "bf16"):
        return None, "selected_operator_is_not_the_declared_mxfp8_qbmm"
    m, n, k = (int(value) for value in op.local_shape)
    if n % 32 or k % 16:
        return None, "qbmm_weight_device_shape_not_divisible"
    pairs = ((k + 31) // 32 + 1) // 2
    abi = native_abi_from_slots(
        "QuantBatchMatmulV3",
        [
            {"shape": [m, k], "dtype": "fp8_e4m3", "layout": "ND"},
            {"shape": [n // 32, k // 16, 16, 32], "dtype": "fp8_e4m3",
             "layout": "FRACTAL_NZ"},
            {"shape": [pairs, n, 2], "dtype": "fp8_e8m0", "layout": "ND"},
            {"shape": [m, pairs, 2], "dtype": "fp8_e8m0", "layout": "ND"},
        ],
        [{"shape": [m, n], "dtype": "bf16", "layout": "ND"}],
    )
    if abi.get("status") != "complete":
        return None, "qbmm_abi_slots_incomplete"
    return abi, None


from functools import lru_cache


@lru_cache(maxsize=8)
def _parsed_sim_case(model: str, hardware: str, quant: str):
    supply = _sim_supply()
    from mindie_sim.compose import compose_case
    from mindie_sim.observations.calibration import apply_profiler_supply
    from mindie_sim.prediction.structure import parse_case

    composed = compose_case(
        model, hardware,
        tp=1, dp=1, ep=1, quant=quant, prompt_tokens=1024,
        output_tokens=1, concurrency=1, layers=1,
        num_devices=1, ranks_per_node=1,
    )
    bound = apply_profiler_supply(
        composed, str(supply), recipe="output", hardware=hardware, owners=None)
    return parse_case(bound)


@lru_cache(maxsize=16)
def _sim_predictions_cached(canonical_json: str):
    request_rows = json.loads(canonical_json)
    _sim_supply()
    from mindie_sim import operator_costs
    from mindie_sim.prediction.operator_analysis import target_operators

    predictions = []
    for request in request_rows:
        request_abi = request["abi"]
        conditions = request["conditions"]
        missing = [key for key in ("hardware", "model", "quant")
                   if not isinstance(conditions.get(key), str)
                   or not conditions[key].strip()]
        if missing:
            predictions.append({
                "prediction_id": "mindie-sim:unmodeled:" + request["request_id"],
                "request_id": request["request_id"], "status": "unmodeled",
                "unmodeled_reason": "conditions_missing:" + ",".join(missing),
                "evidence": ["no_default_model_or_quantization"],
            })
            continue
        hardware = conditions["hardware"]
        tokens = int(request_abi["inputs"][0]["shape"][0])
        case = _parsed_sim_case(conditions["model"], hardware, conditions["quant"])
        op = next(
            item for item in target_operators(
                case, phase="prefill", tokens=tokens, context=0)
            if item.recipe == "output")
        abi, abi_gap = _qbmm_abi_from_op(op)
        if abi is None:
            predictions.append({
                "prediction_id": "mindie-sim:unmodeled:" + request["request_id"],
                "request_id": request["request_id"], "status": "unmodeled",
                "unmodeled_reason": abi_gap,
                "evidence": ["selected_operator_identity_not_qbmm"],
            })
            continue
        row = operator_costs(case, (op,))["operators"][0]
        predictions.append({
            "prediction_id": "mindie-sim:" + request["request_id"],
            "request_id": request["request_id"],
            "duration_ms": float(row["duration_ms"]),
            "status": "modeled",
            "boundary": {
                "kind": "kernel", "native_operator": "QuantBatchMatmulV3",
                "scope": "one_complete_kernel_event",
                "expansion": "single_kernel_row",
            },
            "abi": abi,
            "conditions": dict(conditions),
            "occurrence": dict(request.get("occurrence") or {}),
            "clock": dict(request.get("clock") or {}),
            "window_id": request.get("window_id")
            or (request.get("timing") or {}).get("window_id"),
            "evidence": [
                "mindie_sim.operator_costs(measured dual-load mac_service)",
                "selected_operator=output:gemm:fp8_block1x32_fp8_e8m0",
                "calibration_fixture=r64_qbmm_dual_load/supply.json",
                "same_capture_calibration_not_heldout",
                "request_contains_no_observed_duration",
            ],
        })
    return predictions


def _sim_predictions(request_rows):
    """Bind the selected sim output operator to the full r64 QBMM ABI."""
    return deepcopy(_sim_predictions_cached(json.dumps(request_rows, sort_keys=True)))


def _sim_identity(observation):
    conditions = dict(observation["conditions"])
    block_num = (observation.get("evidence") or {}).get("block_num")
    if block_num is not None and "block_num" not in conditions:
        conditions["block_num"] = block_num
    return {
        "native_operator": observation["boundary"]["native_operator"],
        "native_abi_sha256": observation["abi"]["digest"],
        "boundary": observation["boundary"]["kind"],
        "scope": observation["boundary"].get("scope"),
        "expansion": observation["boundary"].get("expansion"),
        "rank": observation["occurrence"].get("rank"),
        "device_id": observation["occurrence"].get("device_id"),
        "stream": observation["occurrence"].get("stream_id"),
        "clock_domain": observation["clock"].get("domain"),
        "window_id": observation["timing"].get("window_id"),
        "conditions": conditions,
        "fusion_members": observation["fusion"]["members"],
    }


def _sim_prediction_identity(prediction):
    conditions = dict(prediction.get("conditions") or {})
    boundary = prediction.get("boundary") or {}
    abi = prediction.get("abi") or {}
    occurrence = prediction.get("occurrence") or {}
    clock = prediction.get("clock") or {}
    return {
        "native_operator": boundary.get("native_operator"),
        "native_abi_sha256": abi.get("digest"),
        "boundary": boundary.get("kind"),
        "scope": boundary.get("scope"),
        "expansion": boundary.get("expansion"),
        "rank": occurrence.get("rank"),
        "device_id": occurrence.get("device_id"),
        "stream": occurrence.get("stream_id"),
        "clock_domain": clock.get("domain"),
        "window_id": prediction.get("window_id")
        or (prediction.get("timing") or {}).get("window_id"),
        "conditions": conditions,
        "fusion_members": (boundary.get("fusion") or {}).get("members", ()),
    }


def _sim_campaign(exported, predictions):
    samples = []
    for observation in exported["observations"]:
        samples.append({
            "sample_id": observation["observation_id"],
            "request_id": observation["request_id"],
            "run_id": observation["timing"]["window_id"],
            "duration_ms": observation["timing"]["duration_ms"],
            "identity": _sim_identity(observation),
            "source": observation["source"],
            "split": "calibration",
            "metadata": {},
        })
    rows = [{
        "prediction_id": prediction["prediction_id"],
        "request_id": prediction["request_id"],
        "duration_ms": prediction["duration_ms"],
        "identity": _sim_prediction_identity(prediction),
        "evidence": prediction["evidence"],
    } for prediction in predictions]
    return {"observations": samples, "predictions": rows,
            "cohort_role": "same_capture_calibration_not_heldout"}


def test_export_reads_real_capture_without_importing_sim(monkeypatch, exported):
    assert exported["schema"] == NATIVE_OBSERVATION_SCHEMA
    assert exported["counts"] == {
        "events": 2, "confirmed": 2, "candidate": 0, "unidentified": 0,
        "requests": 2, "windows": 2, "devices": 1,
        "missing_device_id": 0, "missing_native_type": 0,
        "missing_stream_id": 0,
    }
    assert exported["window"]["kind"] == "per_domain"
    assert len(exported["windows"]) == 2
    assert {round(row["duration_ms"], 6) for row in exported["windows"]} == {
        0.034665, 0.246132}
    assert exported["truncated"] is False
    assert exported["source_identity"]["sha256"] == json.loads(
        PROVENANCE.read_text())["fixture_csv_sha256"]
    assert all(row["abi"]["status"] == "complete" for row in exported["observations"])
    assert all(row["clock"]["comparable"] is False for row in exported["observations"])
    assert all(row["boundary"]["kind"] == "kernel" for row in exported["observations"])
    assert all(row["boundary"]["expansion_status"]
               == "api_call_not_retained_in_kernel_details_csv"
               for row in exported["observations"])

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "mindie_sim" or name.startswith("mindie_sim."):
            raise AssertionError("native observation export must not import sim")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    again = export_native_observations(CAPTURE, **CONDITIONS)
    assert again["counts"] == exported["counts"]
    assert [row["abi"]["digest"] for row in again["observations"]] == [
        row["abi"]["digest"] for row in exported["observations"]]


def test_requests_are_timing_free_and_content_addressed(requests, exported):
    assert requests["schema"] == NATIVE_REQUEST_SCHEMA
    assert requests["counts"] == {"requests": 2, "observations": 2}
    payload = json.dumps(requests["requests"], sort_keys=True)
    for forbidden in ("duration_ms", "duration_ns", "observed_ms",
                      "start_ns", "end_ns", "pipe_times_us"):
        assert forbidden not in payload
    digests = {row["abi"]["digest"] for row in exported["observations"]}
    assert {row["abi"]["digest"] for row in requests["requests"]} == digests
    assert all(row["request_id"].startswith("request:")
               for row in requests["requests"])


def test_real_native_cohort_keeps_per_item_pass_and_failure(exported, requests):
    predictions = _sim_predictions(requests["requests"])
    report = compare_native_predictions(exported, predictions)
    assert report["schema"] == NATIVE_COMPARISON_SCHEMA
    assert report["counts"]["paired"] == 2
    assert report["counts"]["unpaired_observations"] == 0
    assert report["counts"]["unpaired_predictions"] == 0

    assert report["counts"]["family_aggregates_used"] == 0
    assert report["counts"]["fused_members_allocated"] == 0
    assert report["status"] == "failed"

    tail = next(row for row in report["items"] if row["observed_ms"] < 0.1)
    full = next(row for row in report["items"] if row["observed_ms"] > 0.1)
    assert tail["status"] == "outside_tolerance"
    assert abs(tail["comparison"]["relative_error"]) > 0.10
    assert full["status"] == "within_tolerance"
    assert abs(full["comparison"]["relative_error"]) <= 0.10
    assert full["comparison"]["denominator"] == "observed_ms"
    assert full["observation_samples"] == 1
    assert full["observation_clock_domains"] == ["device:2:stream:61"]

    failure = next(
        row for row in report["failure_matrix"]
        if row["reason"] == "relative_error_exceeds_tolerance")
    assert failure["root_cause"] == "unclassified_residual"
    assert failure["count"] == 1
    assert failure["evidence"]["observed_ms"] == tail["observed_ms"]
    assert failure["evidence"]["predicted_ms"] == tail["predicted_ms"]
    assert failure["evidence"]["observation_evidence"]["pipe_times_us"][0]
    assert failure["claim"] == "candidate_dimension_not_proven_root_cause"
    assert "family_mean" not in json.dumps(report)


def test_name_only_and_unseen_shape_never_pair(exported):
    source = exported["observations"][0]
    shape = [2, 16384]
    abi = native_abi_from_slots(
        source["boundary"]["native_operator"],
        [
            {"shape": shape, "dtype": "fp8_e4m3", "layout": "ND"},
            {"shape": [192, 1024, 16, 32], "dtype": "fp8_e4m3", "layout": "FRACTAL_NZ"},
            {"shape": [256, 6144, 2], "dtype": "fp8_e8m0", "layout": "ND"},
            {"shape": [2, 256, 2], "dtype": "fp8_e8m0", "layout": "ND"},
        ],
        [{"shape": [2, 6144], "dtype": "bf16", "layout": "ND"}],
    )
    assert abi["digest"] not in {
        row["abi"]["digest"] for row in exported["observations"]}
    prediction = {
        "prediction_id": "same-name-only",
        "duration_ms": 0.034,
        "status": "modeled",
        "boundary": {
            "kind": "kernel",
            "native_operator": source["boundary"]["native_operator"],
        },
        "abi": abi,
        "conditions": {
            "hardware": source["conditions"]["hardware"],
            "phase": source["conditions"]["phase"],
            "model": source["conditions"].get("model"),
            "quant": source["conditions"].get("quant"),
        },
        "occurrence": {"stream_id": source["occurrence"]["stream_id"]},
    }
    report = compare_native_predictions(exported, [prediction])
    assert report["counts"]["paired"] == 0
    assert report["counts"]["name_only_matches"] == 0
    assert report["counts"]["unpaired_observations"] == 2
    assert report["unpaired_predictions"][0]["reason"] == "no_exact_observation_identity"
    assert report["status"] == "inconclusive"


def test_fused_boundary_is_compared_once_and_never_allocated(exported):
    abi = native_abi_from_slots(
        "SyntheticFusedKernel",
        [{"shape": [4], "dtype": "bf16", "layout": "ND"}],
        [{"shape": [4], "dtype": "bf16", "layout": "ND"}],
    )
    conditions = dict(exported["observations"][0]["conditions"])
    observation = {
        "schema": "mindie-profiler-native-observation/1",
        "observation_id": "observation:fused", "request_id": "request:fused",
        "boundary": {
            "kind": "kernel", "native_operator": "SyntheticFusedKernel",
            "scope": "one_complete_kernel_event", "expansion": "single_kernel_row",
            "fusion": {"status": "observed_fused",
                       "members": ["node:a", "node:b"], "member_count": 2,
                       "allocation": "none"},
        },
        "abi": abi, "conditions": conditions,
        "occurrence": {"rank": None, "device_id": "2", "stream_id": "7"},
        "clock": {"domain": "device:2:stream:7", "comparable": False,
                  "reference_domain": None},
        "timing": {"duration_ms": 0.010, "duration_ns": 10000,
                   "complete_in_window": True, "window_id": "window:fused"},
        "structure": {"status": "confirmed", "basis": "synthetic_contract"},
        "evidence": {}, "fusion": {
            "status": "observed_fused", "members": ["node:a", "node:b"],
            "member_count": 2, "allocation": "none"},
    }
    fused = {"observations": [observation]}
    requests = native_prediction_requests(fused)["requests"]
    assert requests[0]["boundary"]["fusion"]["members"] == ["node:a", "node:b"]

    fused_prediction = {
        "prediction_id": "fused", "request_id": requests[0]["request_id"],
        "duration_ms": 0.010, "status": "modeled",
        "boundary": {"kind": "kernel", "native_operator": "SyntheticFusedKernel",
                     "scope": "one_complete_kernel_event",
                     "expansion": "single_kernel_row",
                     "fusion": {"members": ["node:a", "node:b"]}},
        "abi": abi,
        "conditions": dict(requests[0]["conditions"]),
        "occurrence": dict(requests[0]["occurrence"]),
        "clock": dict(requests[0]["clock"]),
        "window_id": requests[0]["window_id"],
    }
    matched = compare_native_predictions(
        fused, [fused_prediction], requests=requests)
    assert matched["counts"]["paired"] == 1
    assert matched["items"][0]["boundary"]["fusion"]["members"] == ["node:a", "node:b"]
    assert matched["counts"]["fused_members_allocated"] == 0

    per_member_request = deepcopy(requests[0])
    per_member_request["boundary"]["fusion"] = {
        "status": "not_evidenced", "members": [], "member_count": 1,
    }
    per_member = {
        "prediction_id": "per-member",
        "request_id": per_member_request["request_id"],
        "duration_ms": 0.010, "status": "modeled",
        "boundary": {"kind": "kernel", "native_operator": "SyntheticFusedKernel",
                     "scope": "one_complete_kernel_event",
                     "expansion": "single_kernel_row",
                     "fusion": {"members": []}},
        "abi": abi,
        "conditions": dict(per_member_request["conditions"]),
        "occurrence": dict(per_member_request["occurrence"]),
        "clock": dict(per_member_request["clock"]),
        "window_id": per_member_request["window_id"],
    }
    rejected = compare_native_predictions(
        fused, [per_member], requests=[per_member_request])
    assert rejected["counts"]["paired"] == 0
    assert rejected["unpaired_observations"][0]["reason"] == "fusion_boundary_mismatch"
    assert rejected["unpaired_predictions"][0]["reason"] == "fusion_boundary_mismatch"
    assert rejected["counts"]["fused_members_allocated"] == 0


def test_candidate_and_duplicate_predictions_stay_inconclusive(exported, requests):
    candidate = deepcopy(exported)
    candidate["observations"] = [deepcopy(exported["observations"][0])]
    candidate["observations"][0]["structure"] = {
        "status": "candidate", "basis": "partial_native_tensor_abi",
        "ambiguity": [{"slot": "inputs[3]", "reason": "missing_dtype"}],
    }
    request = native_prediction_requests(candidate)["requests"][0]
    report = compare_native_predictions(
        candidate,
        [{"prediction_id": "candidate", "request_id": request["request_id"],
          "duration_ms": 0.03, "status": "modeled"}],
        requests=[request],
    )
    assert report["counts"]["paired"] == 0
    assert report["unpaired_observations"][0]["reason"] == "candidate_observation_structure"
    assert report["unpaired_observations"][0]["structure_status"] == "candidate"
    assert report["status"] == "inconclusive"

    duplicate = compare_native_predictions(
        exported,
        [
            {"prediction_id": "a",
             "request_id": requests["requests"][0]["request_id"],
             "duration_ms": 0.03, "status": "modeled"},
            {"prediction_id": "b",
             "request_id": requests["requests"][0]["request_id"],
             "duration_ms": 0.04, "status": "modeled"},
        ],
        requests=requests,
    )
    assert duplicate["counts"]["paired"] == 0
    assert duplicate["ambiguous"][0]["reason"] == "ambiguous_predictions"
    assert duplicate["status"] == "inconclusive"


def test_sim_descriptive_report_matches_profiler_pair_set(exported, requests):
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report

    predictions = _sim_predictions(requests["requests"])
    report = native_comparison_report(_sim_campaign(exported, predictions))
    assert report["schema"] == "mindie-sim.native-comparison/1"
    assert report["status"] == "completed"
    assert report["coverage"]["paired"] == 2
    assert report["coverage"]["unpaired_observations"] == 0
    assert "within_tolerance" not in json.dumps(report)
    tail = next(row for row in report["points"] if row["observed_ms"] < 0.1)
    full = next(row for row in report["points"] if row["observed_ms"] > 0.1)
    assert tail["comparison"]["relative_error"] == pytest.approx(
        (tail["predicted_ms"] - tail["observed_ms"]) / tail["observed_ms"],
        rel=1e-12)
    assert full["comparison"]["relative_error"] == pytest.approx(
        (full["predicted_ms"] - full["observed_ms"]) / full["observed_ms"],
        rel=1e-12)
    assert all(sample["split"] == "calibration" for sample in _sim_campaign(
        exported, predictions)["observations"])
    assert report["cohort_role"] == "same_capture_calibration_not_heldout"
    assert report["fixed_boundary"]["denominator"] == "observed_ms"
    assert report["fixed_boundary"]["family_average_allowed"] is False


def test_cli_native_mode_and_timing_free_request_output(
        exported, requests, tmp_path, monkeypatch):
    observation_path = tmp_path / "observations.json"
    prediction_path = tmp_path / "predictions.json"
    output_path = tmp_path / "comparison.json"
    observation_path.write_text(json.dumps(exported))
    prediction_path.write_text(json.dumps({"predictions": _sim_predictions(
        requests["requests"])}))

    code = main([
        "--native-observations", str(observation_path),
        "--predictions", str(prediction_path),
        "--output", str(output_path),
    ])
    assert code == 3
    result = json.loads(output_path.read_text())
    assert result["schema"] == NATIVE_COMPARISON_SCHEMA
    assert result["status"] == "failed"

    request_path = tmp_path / "requests.json"
    code = main([
        "--native-observations", str(CAPTURE),
        "--requests-output", str(request_path),
        "--hardware", CONDITIONS["hardware"],
        "--phase", CONDITIONS["phase"],
        "--model", CONDITIONS["model"],
        "--quant", CONDITIONS["quant"],
    ])
    assert code == 0
    payload = json.loads(request_path.read_text())
    assert payload["schema"] == NATIVE_REQUEST_SCHEMA
    assert payload["counts"]["requests"] == 2
    assert "duration_ms" not in json.dumps(payload["requests"])

    tail = deepcopy(exported)
    tail["observations"] = [
        row for row in exported["observations"]
        if row["timing"]["duration_ms"] < 0.1
    ]
    tail_request = native_prediction_requests(tail)["requests"][0]
    tail_prediction = _sim_predictions([tail_request])[0]
    tail["scope"] = {
        "window_ids": [tail["observations"][0]["timing"]["window_id"]],
        "event_count": 1,
        "parent_capture_id": (exported["source_identity"].get("sha256")
                              or exported["source_identity"]["path"]),
    }
    tail_observation_path = tmp_path / "tail-observations.json"
    tail_prediction_path = tmp_path / "tail-predictions.json"
    tail_output = tmp_path / "tail-comparison.json"
    tail_observation_path.write_text(json.dumps(tail))
    tail_prediction_path.write_text(json.dumps({"predictions": [tail_prediction]}))
    code = main([
        "--native-observations", str(tail_observation_path),
        "--predictions", str(tail_prediction_path),
        "--output", str(tail_output),
    ])
    assert code == 3
    assert json.loads(tail_output.read_text())["status"] == "failed"


def test_one_outside_sample_cannot_hide_behind_a_passing_median(exported):
    source = exported["observations"][0]
    observations = {"observations": []}
    for index, duration_ms in enumerate((0.030, 0.030, 0.060)):
        row = deepcopy(source)
        row["observation_id"] = f"observation:sample-{index}"
        row["timing"]["duration_ms"] = duration_ms
        row["timing"]["duration_ns"] = int(duration_ms * 1_000_000)
        observations["observations"].append(row)
    request = native_prediction_requests(observations)["requests"][0]
    prediction = {
        "prediction_id": "median-passer", "request_id": request["request_id"],
        "duration_ms": 0.0315, "status": "modeled",
        "abi": source["abi"],
        "boundary": dict(request["boundary"]),
        "conditions": dict(request["conditions"]),
        "occurrence": dict(request["occurrence"]),
        "clock": dict(request["clock"]),
        "window_id": request["window_id"],
    }
    report = compare_native_predictions(
        observations, [prediction], requests=[request])
    item = report["items"][0]
    assert item["status"] == "outside_tolerance"
    assert item["observed_ms"] == pytest.approx(0.030)
    assert abs(item["comparison"]["relative_error"]) <= 0.10
    assert item["comparison"]["within_tolerance"] is False
    assert item["comparison"]["outside_sample_ids"] == ["observation:sample-2"]
    assert report["counts"]["observations_within_tolerance"] == 2
    assert report["counts"]["observations_outside_tolerance"] == 1


def test_real_incomplete_tensor_row_stays_a_candidate_not_a_confirmed_match():
    capture = ROOT / "tests/fixtures/structure_contracts/a5_tensor_contracts.csv"
    exported = export_native_observations(
        capture, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    assert exported["counts"]["candidate"] == 1
    candidate = next(
        row for row in exported["observations"]
        if row["structure"]["status"] == "candidate")
    assert candidate["abi"]["status"] == "incomplete"
    assert candidate["boundary"]["native_operator"] == "fused_gdn_gating_kernel"
    observation = {
        "observations": [{
            **candidate,
            "timing": {**candidate["timing"], "duration_ms": 0.1},
        }]
    }
    report = compare_native_predictions(observation, [])
    assert report["counts"]["paired"] == 0
    assert report["unpaired_observations"][0]["reason"] == "native_abi_incomplete"
    assert report["unpaired_observations"][0]["structure_status"] == "candidate"


def test_event_budget_truncation_is_explicit():
    exported = export_native_observations(CAPTURE, max_events=1, **CONDITIONS)
    assert exported["counts"]["events"] == 1
    assert exported["truncated"] is True
    assert "event_budget_truncated" in exported["limitations"]


def test_unmodeled_prediction_keeps_its_gap_instead_of_crashing(exported, requests):
    request = requests["requests"][0]
    report = compare_native_predictions(
        exported,
        [{"prediction_id": "unmodeled-gap", "request_id": request["request_id"],
          "status": "unmodeled", "unmodeled_reason": "native_entry_not_bound"}],
        requests=requests,
    )
    assert report["counts"]["paired"] == 0
    assert report["unpaired_predictions"][0]["predicted_ms"] is None
    assert report["unpaired_predictions"][0]["reason"].startswith("prediction_unmodeled:")
    assert report["status"] == "inconclusive"


def test_multiple_capture_candidates_are_not_silently_selected(tmp_path):
    for rank in ("rank_0", "rank_1"):
        target = tmp_path / rank
        target.mkdir()
        shutil.copyfile(CAPTURE, target / "kernel_details.csv")
    with pytest.raises(ProfilerUsageError, match="multiple ranks have kernel_details"):
        export_native_observations(tmp_path, **CONDITIONS)


def test_sim_descriptive_report_keeps_unmodeled_prediction_gap(exported):
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report

    observation = exported["observations"][0]
    campaign = {
        "observations": [{
            "sample_id": observation["observation_id"],
            "request_id": observation["request_id"],
            "run_id": observation["timing"]["window_id"],
            "duration_ms": observation["timing"]["duration_ms"],
            "identity": _sim_identity(observation),
            "source": observation["source"],
            "split": "calibration",
            "metadata": {},
        }],
        "predictions": [{
            "prediction_id": "sim-unmodeled",
            "request_id": observation["request_id"],
            "status": "unmodeled",
            "unmodeled_reason": "native_entry_not_bound",
            "identity": _sim_identity(observation),
        }],
    }
    report = native_comparison_report(campaign)
    assert report["coverage"]["paired"] == 0
    assert report["unpaired_predictions"][0]["reason"].startswith("prediction_unmodeled:")
    assert report["status"] == "partial"


def test_sim_descriptive_report_keeps_fusion_boundary_mismatch(exported):
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report

    observation = deepcopy(exported["observations"][0])
    observation["boundary"]["fusion"] = {
        "status": "observed_fused", "members": ["node:a", "node:b"],
        "member_count": 2, "allocation": "none",
    }
    observation["fusion"] = observation["boundary"]["fusion"]
    fused_identity = _sim_identity(observation)
    single_identity = {**fused_identity, "fusion_members": []}
    campaign = {
        "observations": [{
            "sample_id": "fused-sample", "request_id": observation["request_id"],
            "run_id": observation["timing"]["window_id"],
            "duration_ms": observation["timing"]["duration_ms"],
            "identity": fused_identity, "source": observation["source"],
            "split": "calibration", "metadata": {},
        }],
        "predictions": [{
            "prediction_id": "per-member", "request_id": observation["request_id"],
            "duration_ms": observation["timing"]["duration_ms"],
            "identity": single_identity,
        }],
    }
    report = native_comparison_report(campaign)
    assert report["coverage"]["paired"] == 0
    assert report["not_comparable"][0]["reason"] == "fusion_boundary_mismatch"
    assert report["not_comparable"][0]["observation_ids"] == ["fused-sample"]
    assert report["not_comparable"][0]["observed_ms"] == pytest.approx(
        observation["timing"]["duration_ms"])
    assert report["unpaired_predictions"][0]["reason"] == "no_exact_observation_identity"


T03_FIRST_CALL = Path(os.environ.get(
    "MINDIE_T03_NATIVE_FIRST_CALL",
    "capture://codex/2026-11-12/kan-x/work/a5-implementation/jobs/"
    "A5-T03/out/native/native_first_call.json"))


def test_t03_first_call_abi_is_ingestible_but_conditions_are_incomplete():
    if not T03_FIRST_CALL.is_file():
        pytest.skip(f"T03 native first call unavailable: {T03_FIRST_CALL}")
    record = json.loads(T03_FIRST_CALL.read_text())
    if record.get("native_operator_type") != "CausalConv1d":
        pytest.skip("T03 first-call selection changed; keep the snapshot hash")
    abi = native_abi_from_slots(
        record["native_operator_type"],
        record["raw_abi"]["inputs"], record["raw_abi"]["outputs"])
    assert abi["status"] == "complete"
    assert len(abi["inputs"]) == 12
    assert "undefined" in {slot["quality"] for slot in abi["inputs"]}
    observation = {
        "schema": "mindie-profiler-native-observation/1",
        "observation_id": "observation:t03-first",
        "request_id": "request:t03-first",
        "boundary": {
            "kind": "kernel",
            "native_operator": record["native_operator_type"],
            "scope": "one_complete_kernel_event",
            "expansion": "single_kernel_row",
        },
        "abi": abi,
        "conditions": {"model": record["case_id"]},
        "occurrence": {
            "rank": None,
            "device_id": record["observation_window"]["example_locator"]["device_id"],
            "stream_id": record["observation_window"]["example_locator"]["stream_id"],
            "task_id": record["observation_window"]["example_locator"]["task_id"],
        },
        "clock": {
            "domain": record["clock"]["domain"], "comparable": False,
            "reference_domain": None,
        },
        "timing": {
            "duration_ms": record["clock"]["duration_us"] / 1000.0,
            "window_id": "window:t03-cohort",
        },
        "structure": {"status": "confirmed", "basis": "complete_ordered_tensor_slots"},
        "evidence": {"cohort_window": record["observation_window"]},
        "fusion": {"members": [], "status": "not_evidenced"},
    }
    report = compare_native_predictions(
        {"observations": [observation]},
        [{"prediction_id": "t03-prediction", "request_id": "request:t03-first",
          "duration_ms": record["clock"]["duration_us"] / 1000.0,
          "status": "modeled"}],
    )
    assert report["counts"]["paired"] == 0
    assert report["unpaired_observations"][0]["reason"] == "condition_missing:hardware"
    assert "hardware" in report["unpaired_observations"][0]["reason"]


def _tail_prediction(exported, requests):
    predictions = _sim_predictions(requests["requests"])
    return predictions, predictions[0]


def test_same_m_changed_k_or_layout_is_not_native_bound(exported, requests):
    predictions, _ = _tail_prediction(exported, requests)
    tail_observations = [row for row in exported["observations"]
                         if row["timing"]["duration_ms"] < 0.1]
    tail_request = [row for row in requests["requests"]
                    if row["occurrence"]["stream_id"]
                    == tail_observations[0]["occurrence"]["stream_id"]]
    tail_exported = {"observations": tail_observations,
                     "window": exported["window"], "truncated": False}
    changed_shape = deepcopy(tail_request)
    changed_shape[0]["abi"]["inputs"][0]["shape"] = [1, 8192]
    report = compare_native_predictions(
        tail_exported, [predictions[0]], requests=changed_shape)
    assert report["counts"]["paired"] == 0
    assert report["counts"]["predictions_with_abi_conflict"] >= 1
    assert any(any(conflict.startswith("abi.")
                   for conflict in row["conflicts"])
               for row in report["unpaired_predictions"])
    assert report["unpaired_observations"][0]["observation_ids"] == [
        tail_observations[0]["observation_id"]]

    changed_layout = deepcopy(tail_request)
    changed_layout[0]["abi"]["inputs"][1]["layout"] = "ND"
    report = compare_native_predictions(
        tail_exported, [predictions[0]], requests=changed_layout)
    assert report["counts"]["paired"] == 0
    assert any(row["conflicts"] for row in report["unpaired_predictions"])


def test_request_only_prediction_is_not_independent_native_identity(exported, requests):
    request = requests["requests"][0]
    prediction = {
        "prediction_id": "request-only", "request_id": request["request_id"],
        "duration_ms": exported["observations"][0]["timing"]["duration_ms"],
        "status": "modeled",
    }
    report = compare_native_predictions(exported, [prediction], requests=requests)
    assert report["counts"]["paired"] == 0
    assert report["counts"]["predictions_without_independent_abi"] == 1
    assert report["unpaired_predictions"][0]["reason"] == "prediction_abi_not_declared"
    assert report["unpaired_predictions"][0]["abi_declared"] is False


def test_stale_digest_with_modified_slots_is_recomputed_and_rejected(exported, requests):
    predictions, _ = _tail_prediction(exported, requests)
    prediction = deepcopy(predictions[0])
    prediction["abi"]["inputs"][0]["shape"] = [2, 16384]
    prediction = json.loads(json.dumps(prediction))
    report = compare_native_predictions(exported, [prediction], requests=requests)
    assert report["counts"]["paired"] == 0
    assert any("abi.digest" in row["conflicts"]
               for row in report["unpaired_predictions"])
    assert report["unpaired_predictions"][0]["abi_verified"] is False
    second = compare_native_predictions(
        json.loads(json.dumps(exported)), [json.loads(json.dumps(prediction))],
        requests=json.loads(json.dumps(requests)))
    assert second["counts"]["paired"] == 0
    assert second["unpaired_predictions"][0]["abi_verified"] is False

    # Recomputing a different slot order must produce a different digest.
    swapped = native_abi_from_slots(
        prediction["abi"]["native_operator"],
        list(reversed(prediction["abi"]["inputs"])),
        prediction["abi"]["outputs"],
    )
    assert swapped["digest"] != exported["observations"][0]["abi"]["digest"]


def test_scalar_empty_slot_without_explicit_dtype_layout_is_incomplete():
    incomplete = native_abi_from_slots(
        "SyntheticScalar",
        [{"shape": []}],
        [{"shape": [1], "dtype": "bf16", "layout": "ND"}],
    )
    assert incomplete["status"] == "incomplete"
    assert incomplete["digest"] is None
    assert any(item["reason"] in {"missing_dtype", "missing_layout",
                                  "missing_dtype_layout_for_empty_slot"}
               for item in incomplete["issues"])
    explicit = native_abi_from_slots(
        "SyntheticScalar",
        [{"shape": [], "dtype": None, "layout": None}],
        [{"shape": [1], "dtype": "bf16", "layout": "ND"}],
    )
    assert explicit["status"] == "complete"


def test_request_id_cannot_override_device_or_explicit_empty_fusion(exported, requests):
    predictions, _ = _tail_prediction(exported, requests)
    wrong_device = deepcopy(predictions[0])
    wrong_device["occurrence"] = {"rank": None, "device_id": "99", "stream_id": "21"}
    report = compare_native_predictions(
        exported, [wrong_device], requests=requests)
    assert report["counts"]["paired"] == 0
    assert any("occurrence.device_id" in conflict
               for conflict in report["unpaired_predictions"][0]["conflicts"])
    assert report["unpaired_observations"][0]["observation_ids"]

    # Explicit empty members must conflict with a fused request, not inherit.
    fused = deepcopy(exported)
    fused["observations"] = [deepcopy(exported["observations"][0])]
    fused["observations"][0]["boundary"]["fusion"] = {
        "status": "observed_fused", "members": ["node:a", "node:b"],
        "member_count": 2, "allocation": "none",
    }
    fused["observations"][0]["fusion"] = fused["observations"][0]["boundary"]["fusion"]
    fused_request = native_prediction_requests(fused)["requests"][0]
    fused_prediction = {
        "prediction_id": "explicit-empty", "request_id": fused_request["request_id"],
        "duration_ms": fused["observations"][0]["timing"]["duration_ms"],
        "status": "modeled",
        "boundary": {**fused["observations"][0]["boundary"],
                     "fusion": {"members": [], "status": "not_evidenced"}},
        "abi": fused["observations"][0]["abi"],
    }
    rejected = compare_native_predictions(
        fused, [fused_prediction], requests=[fused_request])
    assert rejected["counts"]["paired"] == 0
    assert any("boundary.fusion_members" in conflict
               for conflict in rejected["unpaired_predictions"][0]["conflicts"])


def test_formal_tolerance_is_fixed_and_cannot_be_relaxed(exported, requests, tmp_path):
    predictions, _ = _tail_prediction(exported, requests)
    report = compare_native_predictions(
        exported, predictions,
        diagnostic_tolerance={"relative": 0.5, "absolute_ms": 0.052},
    )
    assert report["status"] == "failed"
    assert report["counts"]["outside_tolerance"] == 1
    outside = [row for row in report["items"]
               if row["comparison"]["within_tolerance"] is False]
    assert outside
    assert all(abs(row["comparison"]["relative_error"]) > 0.1 for row in outside)
    assert all(row["comparison"]["formal_policy"]
               == "fixed_itemwise_10pct_no_absolute_allowance"
               for row in report["items"])
    assert all(row["diagnostic_within"] for row in report["items"][0][
        "comparison"]["sample_verdicts"])
    assert report["tolerance"]["formal"]["absolute_ms"] == 0.0

    prediction_path = tmp_path / "predictions.json"
    output_path = tmp_path / "comparison.json"
    prediction_path.write_text(json.dumps({"predictions": predictions}))
    code = main([
        "--native-observations", str(CAPTURE),
        "--predictions", str(prediction_path),
        "--hardware", CONDITIONS["hardware"],
        "--phase", CONDITIONS["phase"],
        "--model", CONDITIONS["model"],
        "--quant", CONDITIONS["quant"],
        "--diagnostic-absolute-ms", "0.052",
        "--output", str(output_path),
    ])
    assert code == 3
    assert json.loads(output_path.read_text())["status"] == "failed"


def test_truncated_observation_window_cannot_pass(exported, requests):
    truncated = export_native_observations(
        CAPTURE, max_events=1, **CONDITIONS)
    assert truncated["truncated"] is True
    request = native_prediction_requests(truncated)["requests"][0]
    prediction = _sim_predictions([request])[0]
    report = compare_native_predictions(
        truncated, [prediction], requests=[request])
    assert report["counts"]["paired"] == 1
    assert report["status"] == "failed"
    assert report["coverage"]["truncated"] is True
    assert report["coverage"]["partial_coverage"] is True
    assert report["items"][0]["status"] == "outside_tolerance"
    assert any(row["reason"] == "partial_observation_window_coverage"
               for row in report["failure_matrix"])


def test_two_devices_same_stream_keep_local_windows_and_no_cross_edges(tmp_path):
    capture = _capture_variant(tmp_path, [
        {"Device_id": "0", "Stream ID": "7", "Start Time(us)": "100.000",
         "Duration(us)": "10.000"},
        {"Device_id": "1", "Stream ID": "7", "Start Time(us)": "2000100.000",
         "Duration(us)": "10.000"},
    ])
    exported = export_native_observations(
        capture, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    assert exported["counts"]["devices"] == 2
    assert len(exported["windows"]) == 2
    assert exported["window"]["kind"] == "per_domain"
    assert "start_ns" not in exported["window"]
    assert "end_ns" not in exported["window"]
    assert {round(row["duration_ms"], 6) for row in exported["windows"]} == {0.01}
    assert all(row["causality"]["stream_predecessor"] is None
               and row["causality"]["stream_successor"] is None
               for row in exported["observations"])


def test_missing_device_and_missing_type_keep_local_duration(tmp_path):
    missing_device = _capture_variant(tmp_path, [{
        "Device_id": "", "Stream ID": "7", "Start Time(us)": "100.000",
        "Duration(us)": "10.000",
    }], name="missing-device.csv")
    exported = export_native_observations(
        missing_device, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    assert exported["counts"]["missing_device_id"] == 1
    observation = exported["observations"][0]
    assert observation["structure"]["status"] == "candidate"
    assert observation["timing"]["duration_ms"] == pytest.approx(0.01)
    assert observation["abi"]["status"] == "complete"
    assert observation["occurrence"]["device_id"] is None

    missing_type = _capture_variant(tmp_path, [{
        "Device_id": "2", "Stream ID": "7", "Start Time(us)": "100.000",
        "Duration(us)": "10.000", "Type": "", "Name": "AI_CORE",
        "Accelerator Core": "AI_CORE",
    }], name="missing-type.csv")
    exported = export_native_observations(
        missing_type, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    assert exported["counts"]["missing_native_type"] == 1
    observation = exported["observations"][0]
    assert observation["structure"]["status"] == "candidate"
    assert observation["boundary"]["native_operator"] is None
    assert observation["boundary"]["raw_kind"] == "AI_CORE"
    assert observation["timing"]["duration_ms"] == pytest.approx(0.01)
    assert observation["abi"]["status"] == "candidate"
    assert observation["abi"]["digest"] is None


def test_native_cli_rank_reaches_csv_export(tmp_path):
    request_path = tmp_path / "requests.json"
    code = main([
        "--native-observations", str(CAPTURE),
        "--requests-output", str(request_path), "--rank", "3",
        "--hardware", CONDITIONS["hardware"], "--phase", CONDITIONS["phase"],
        "--model", CONDITIONS["model"], "--quant", CONDITIONS["quant"],
    ])
    assert code == 0
    requests = json.loads(request_path.read_text())["requests"]
    assert all(row["occurrence"]["rank"] == "3" for row in requests)


def test_sim_request_conflict_preserves_observation_ids(exported):
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report

    observation = exported["observations"][0]
    identity = _sim_identity(observation)
    conflicting = {**identity, "native_abi_sha256": "sha256:" + "0" * 64}
    campaign = {
        "observations": [{
            "sample_id": observation["observation_id"],
            "request_id": observation["request_id"],
            "run_id": "r", "duration_ms": observation["timing"]["duration_ms"],
            "identity": identity, "source": observation["source"],
            "split": "calibration", "metadata": {},
        }],
        "predictions": [{
            "prediction_id": "conflict", "request_id": observation["request_id"],
            "duration_ms": 0.01, "identity": conflicting,
        }],
    }
    report = native_comparison_report(campaign)
    assert report["coverage"]["paired"] == 0
    assert report["not_comparable"][0]["reason"].startswith(
        "request_identity_conflict:")
    assert report["not_comparable"][0]["observation_ids"] == [
        observation["observation_id"]]
    assert report["not_comparable"][0]["observed_ms"] == pytest.approx(
        observation["timing"]["duration_ms"])


def test_abi_fifth_slot_gap_and_conflict_are_not_collapsed(exported, requests):
    source = exported["observations"][0]
    five_inputs = [*source["abi"]["inputs"], {"shape": []}]
    five = native_abi_from_slots(
        source["abi"]["native_operator"], five_inputs, source["abi"]["outputs"])
    assert five["status"] == "incomplete"
    assert len(five["inputs"]) == 5
    assert five["inputs"][-1]["quality"] == "missing"
    assert five["digest"] is None
    again = native_abi_from_slots(
        five["native_operator"], five["inputs"], five["outputs"])
    assert again["status"] == "incomplete"
    assert len(again["inputs"]) == 5
    assert again["issues"] == five["issues"]

    request = next(row for row in requests["requests"]
                   if row["request_id"] == source["request_id"])
    prediction = {
        "prediction_id": "five-slot-gap", "request_id": request["request_id"],
        "duration_ms": source["timing"]["duration_ms"], "status": "modeled",
        "abi": five,
    }
    report = compare_native_predictions(
        {"observations": [source], "window": exported["window"]},
        [prediction], requests=[request])
    assert report["counts"]["paired"] == 0
    assert report["unpaired_predictions"][0]["abi_verified"] is False
    assert len(report["unpaired_predictions"][0]["abi"]["inputs"]) == 5
    assert report["unpaired_observations"][0]["observation_ids"] == [
        source["observation_id"]]

    conflict = {
        **source["abi"], "status": "conflict", "digest": None,
        "declared_digest": source["abi"]["digest"],
        "computed_digest": "sha256:" + "1" * 64,
        "verified": False,
        "issues": [{"slot": "abi.digest", "reason": "abi_digest_mismatch"}],
    }
    prediction["abi"] = conflict
    report = compare_native_predictions(
        {"observations": [source], "window": exported["window"]},
        [prediction], requests=[request])
    assert report["counts"]["paired"] == 0
    assert report["unpaired_predictions"][0]["abi_verified"] is False
    assert report["unpaired_predictions"][0]["conflicts"]
    assert report["unpaired_predictions"][0]["abi"]["declared_digest"] == (
        source["abi"]["digest"])
    assert report["unpaired_predictions"][0]["abi"]["computed_digest"]


def test_abi_presence_undefined_typed_scalar_and_dtype_alias(exported):
    output = [{"shape": [1], "dtype": "bf16", "layout": "ND"}]
    absent = native_abi_from_slots(
        "X", [{"present": False}], output)
    undefined = native_abi_from_slots(
        "X", [{"shape": [], "dtype": None, "layout": None}], output)
    scalar = native_abi_from_slots(
        "X", [{"shape": [], "dtype": "bf16", "layout": "ND"}], output)
    missing = native_abi_from_slots("X", [{"shape": []}], output)
    assert absent["status"] == undefined["status"] == scalar["status"] == "complete"
    assert absent["inputs"][0]["quality"] == "absent"
    assert undefined["inputs"][0]["quality"] == "undefined"
    assert scalar["inputs"][0]["quality"] == "typed_scalar"
    assert len({absent["digest"], undefined["digest"], scalar["digest"]}) == 3
    assert missing["status"] == "incomplete"
    assert missing["inputs"][0]["quality"] == "missing"
    for record in (absent, undefined, scalar):
        again = native_abi_from_slots(
            record["native_operator"], record["inputs"], record["outputs"])
        assert again["status"] == "complete"
        assert again["digest"] == record["digest"]

    source = exported["observations"][0]["abi"]
    alias_inputs = [dict(slot) for slot in source["inputs"]]
    alias_outputs = [dict(slot) for slot in source["outputs"]]
    alias_outputs[0]["dtype"] = "bfloat16"
    alias = native_abi_from_slots(
        source["native_operator"], alias_inputs, alias_outputs)
    assert alias["status"] == "complete"
    assert alias["digest"] == source["digest"]


def test_same_request_samples_dedupe_with_or_without_requests(exported, requests):
    source = exported["observations"][0]
    observations = {"observations": [], "window": exported["window"]}
    for index, duration_ms in enumerate((0.030, 0.030, 0.060)):
        row = deepcopy(source)
        row["observation_id"] = f"observation:dedupe-{index}"
        row["timing"]["duration_ms"] = duration_ms
        row["timing"]["duration_ns"] = int(duration_ms * 1_000_000)
        observations["observations"].append(row)
    request = native_prediction_requests(observations)["requests"][0]
    prediction = {
        "prediction_id": "dedupe", "request_id": request["request_id"],
        "duration_ms": 0.0315, "status": "modeled", "abi": source["abi"],
        "boundary": source["boundary"], "conditions": source["conditions"],
        "occurrence": source["occurrence"], "clock": source["clock"],
        "window_id": source["timing"]["window_id"],
    }
    omitted = compare_native_predictions(observations, [prediction])
    explicit = compare_native_predictions(
        observations, [prediction], requests=[request])
    for report in (omitted, explicit):
        assert report["counts"]["paired"] == 1
        assert report["counts"]["ambiguous"] == 0
        assert report["items"][0]["observation_samples"] == 3
        assert report["items"][0]["status"] == "outside_tolerance"
        assert report["counts"]["observations_outside_tolerance"] == 1
        assert report["status"] == "failed"
    assert (omitted["items"][0]["comparison"]["sample_verdicts"]
            == explicit["items"][0]["comparison"]["sample_verdicts"])


def test_known_execution_is_not_equal_to_missing_or_null(exported):
    source = deepcopy(exported["observations"][0])
    source["conditions"]["execution"] = {"state_version": 1}
    observations = {"observations": [source], "window": exported["window"]}
    request = native_prediction_requests(observations)["requests"][0]
    prediction = {
        "prediction_id": "execution", "request_id": request["request_id"],
        "duration_ms": source["timing"]["duration_ms"], "status": "modeled",
        "abi": source["abi"], "boundary": source["boundary"],
        "conditions": {
            **request["conditions"],
            "execution": {"state_version": 1},
        },
        "occurrence": source["occurrence"], "clock": source["clock"],
        "window_id": source["timing"]["window_id"],
    }
    same = compare_native_predictions(
        observations, [prediction], requests=[request])
    assert same["counts"]["paired"] == 1

    nulled = deepcopy(prediction)
    nulled["conditions"] = {"execution": None}
    null_report = compare_native_predictions(
        observations, [nulled], requests=[request])
    assert null_report["counts"]["paired"] == 0
    assert any("conditions.execution" in conflict
               for conflict in null_report["unpaired_predictions"][0]["conflicts"])

    differing = deepcopy(prediction)
    differing["conditions"] = {"execution": {"state_version": 2}}
    conflict_report = compare_native_predictions(
        observations, [differing], requests=[request])
    assert conflict_report["counts"]["paired"] == 0
    assert any("conditions.execution" in conflict
               for conflict in conflict_report["unpaired_predictions"][0]["conflicts"])

    missing = deepcopy(prediction)
    missing["conditions"] = {}
    missing_report = compare_native_predictions(
        observations, [missing], requests=[request])
    # A short response may reference request conditions only when it also
    # declares the same-time actual consumption evidence.  Silence is a gap.
    assert missing_report["counts"]["paired"] == 0
    assert missing_report["unpaired_predictions"][0]["reason"] == (
        "condition_missing:execution.state_version:"
        "no_actual_consumption_evidence")

    consumed = deepcopy(missing)
    consumed["condition_consumption"] = {
        key: {"value": value, "evidence": ["t12.invocation.conditions"]}
        for key, value in request["conditions"].items()
    }
    consumed_report = compare_native_predictions(
        observations, [consumed], requests=[request])
    assert consumed_report["counts"]["paired"] == 1
    assert consumed_report["items"][0]["condition_gaps"] == []


def test_new_condition_keys_and_explicit_null_are_preserved(exported):
    source = deepcopy(exported["observations"][0])
    source["conditions"] = {
        **source["conditions"],
        "custom_condition": {"nested": 1}, "explicit_null": None,
    }
    window = {
        "id": "window:custom-condition", "kind": "local_domain_range",
        "event_count": 1, "start_ns": 0, "end_ns": 1_000_000,
        "duration_ms": 1.0, "clock_comparable_across_domains": False,
    }
    source["timing"] = {**source["timing"], "window_id": window["id"]}
    observations = {
        "observations": [source],
        "window": {"kind": "per_domain", "count": 1, "windows": [window]},
        "windows": [window],
        "counts": {"events": 1, "confirmed": 1, "candidate": 0,
                   "unidentified": 0, "requests": 1, "windows": 1,
                   "devices": 1, "missing_device_id": 0,
                   "missing_native_type": 0, "missing_stream_id": 0},
        "truncated": False,
    }
    requests = native_prediction_requests(observations)
    request = requests["requests"][0]
    assert request["conditions"]["explicit_null"] is None
    assert request["conditions"]["custom_condition"] == {"nested": 1}

    prediction = {
        "prediction_id": "custom-condition",
        "request_id": request["request_id"],
        "duration_ms": source["timing"]["duration_ms"], "status": "modeled",
        "abi": source["abi"], "boundary": source["boundary"],
        "conditions": deepcopy(source["conditions"]),
        "occurrence": source["occurrence"], "clock": source["clock"],
        "window_id": window["id"],
    }
    report = compare_native_predictions(
        observations, [prediction], requests=requests)
    assert report["counts"]["paired"] == 1
    assert report["items"][0]["condition_gaps"] == []
    assert report["items"][0]["identity"]["conditions"]["explicit_null"] is None

    changed = deepcopy(prediction)
    changed["conditions"]["custom_condition"]["nested"] = 2
    changed_report = compare_native_predictions(
        observations, [changed], requests=requests)
    assert changed_report["counts"]["paired"] == 0
    assert changed_report["unpaired_predictions"][0]["reason"] == (
        "request_identity_conflict:conditions.custom_condition.nested")

    nulled = deepcopy(prediction)
    nulled["conditions"].pop("explicit_null")
    nulled_report = compare_native_predictions(
        observations, [nulled], requests=requests)
    assert nulled_report["counts"]["paired"] == 0
    assert nulled_report["unpaired_predictions"][0]["reason"].startswith(
        "condition_missing:explicit_null:")


def test_input_order_swap_keeps_profiler_and_sim_unpaired_ids(exported):
    source = exported["observations"][0]
    swapped = native_abi_from_slots(
        source["abi"]["native_operator"],
        list(reversed(source["abi"]["inputs"])),
        source["abi"]["outputs"],
    )
    assert swapped["digest"] != source["abi"]["digest"]
    request = next(row for row in native_prediction_requests(exported)["requests"]
                   if row["request_id"] == source["request_id"])
    prediction = {
        "prediction_id": "swapped", "request_id": request["request_id"],
        "duration_ms": source["timing"]["duration_ms"], "status": "modeled",
        "abi": swapped, "boundary": source["boundary"],
        "conditions": source["conditions"], "occurrence": source["occurrence"],
        "clock": source["clock"], "window_id": source["timing"]["window_id"],
    }
    report = compare_native_predictions(
        {"observations": [source], "window": exported["window"]},
        [prediction], requests=[request])
    assert report["counts"]["paired"] == 0
    assert report["unpaired_observations"][0]["observation_ids"] == [
        source["observation_id"]]
    assert report["unpaired_predictions"][0]["prediction_id"] == "swapped"
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report
    sim = native_comparison_report({
        "observations": [{
            "sample_id": source["observation_id"],
            "request_id": source["request_id"], "run_id": "r",
            "duration_ms": source["timing"]["duration_ms"],
            "identity": _sim_identity(source), "source": source["source"],
            "split": "calibration", "metadata": {},
        }],
        "predictions": [{
            "prediction_id": "swapped", "request_id": request["request_id"],
            "duration_ms": source["timing"]["duration_ms"],
            "identity": _sim_prediction_identity(prediction),
        }],
    })
    assert sim["coverage"]["paired"] == 0
    assert sim["not_comparable"][0]["observation_ids"] == [
        source["observation_id"]]
    assert sim["coverage"]["unpaired_predictions"] == 1


def test_deleted_sample_with_full_window_declaration_is_partial(exported, requests, tmp_path):
    tail = deepcopy(exported)
    tail["observations"] = [
        row for row in exported["observations"]
        if row["timing"]["duration_ms"] < 0.1
    ]
    request = native_prediction_requests(tail)["requests"][0]
    prediction = _sim_predictions([request])[0]
    report = compare_native_predictions(
        tail, [prediction], requests=[request])
    assert report["items"][0]["status"] == "outside_tolerance"
    assert report["status"] == "failed"
    assert report["coverage"]["reconciliation"]["missing_events"] == 1
    assert report["coverage"]["reconciliation"]["missing_window_ids"]

    observation_path = tmp_path / "full-declaration.json"
    prediction_path = tmp_path / "prediction.json"
    output_path = tmp_path / "comparison.json"
    observation_path.write_text(json.dumps(tail))
    prediction_path.write_text(json.dumps({"predictions": [prediction]}))
    code = main([
        "--native-observations", str(observation_path),
        "--predictions", str(prediction_path), "--output", str(output_path),
    ])
    assert code == 3
    assert json.loads(output_path.read_text())["status"] == "failed"


def test_missing_stream_does_not_create_causality(tmp_path):
    missing = _capture_variant(tmp_path, [
        {"Device_id": "2", "Stream ID": "", "Start Time(us)": "100.000",
         "Duration(us)": "10.000"},
        {"Device_id": "2", "Stream ID": "", "Start Time(us)": "105.000",
         "Duration(us)": "10.000"},
    ], name="missing-stream.csv")
    exported = export_native_observations(
        missing, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    assert exported["counts"]["missing_stream_id"] == 2
    assert len(exported["windows"]) == 2
    assert {round(row["duration_ms"], 6) for row in exported["windows"]} == {0.01}
    for observation in exported["observations"]:
        assert observation["timing"]["duration_ms"] == pytest.approx(0.01)
        assert observation["abi"]["status"] == "complete"
        assert observation["causality"]["stream_ordinal"] is None
        assert observation["causality"]["dependencies_established"] is False
        assert observation["causality"]["stream_predecessor"] is None
        assert observation["causality"]["stream_successor"] is None
        assert observation["occurrence"]["stream_id"] is None


def test_known_stream_keeps_order_edges(tmp_path):
    known = _capture_variant(tmp_path, [
        {"Device_id": "2", "Stream ID": "7", "Start Time(us)": "100.000",
         "Duration(us)": "10.000"},
        {"Device_id": "2", "Stream ID": "7", "Start Time(us)": "105.000",
         "Duration(us)": "10.000"},
    ], name="known-stream.csv")
    exported = export_native_observations(
        known, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    assert len(exported["windows"]) == 1
    assert exported["windows"][0]["event_count"] == 2
    first, second = exported["observations"]
    assert first["causality"]["stream_successor"] == second["observation_id"]
    assert second["causality"]["stream_predecessor"] == first["observation_id"]
    assert first["causality"]["dependencies_established"] is True


def test_t12_bridge_binds_timing_free_abi_and_preserves_gap(requests):
    pytest.importorskip("mindie_sim")
    from mindie_profiler.sim_bridge import predict_native_requests

    # A complete non-matrix invocation stays an explicit canonical-lowering
    # gap; it is never priced with a generic element-count vector formula.
    invocation = {
        "api": {"namespace": "aclnn", "entry": "aclnnAddRmsNorm",
                "aclnn_symbol": "aclnnAddRmsNorm"},
        "version": {"api": "cann-9.2.0",
                    "image_id": "sha256:9e869e8148467296f56d1001b0dac4fea893c841ac7d0a03d4e824a233c2ffea"},
        "tensors": {
            "x": {"shape": [2048, 5120], "dtype": "bf16", "role": "input"},
            "residual": {"shape": [2048, 5120], "dtype": "bf16", "role": "input"},
            "gamma": {"shape": [5120], "dtype": "bf16", "role": "weight"},
            "output": {"shape": [2048, 5120], "dtype": "bf16", "role": "output"},
            "rstd": {"shape": [2048, 1], "dtype": "fp32", "role": "output"},
            "residual_out": {"shape": [2048, 5120], "dtype": "bf16", "role": "output"},
        },
        "attrs": {"epsilon": 1e-6},
        "conditions": {"variant": "fused_attention_norm",
                       "sequence_rows": "shard", "sequence_ranks": 2},
    }
    positive = predict_native_requests(
        [{"request_id": "req:add-rms", "t12_invocation": invocation}],
        hardware=CONDITIONS["hardware"])
    prediction = positive["predictions"][0]
    assert prediction["status"] == "unmodeled"
    assert prediction["reason"] == (
        "t12_invocation_unavailable:canonical_lowering_missing:aclnnAddRmsNorm")
    assert prediction["duration_ms"] is None
    assert positive["non_claims"] and "no_model_case_constructed" in positive["non_claims"]

    unmodeled_requests = {
        **requests,
        "requests": [
            {**row, "boundary": {**row["boundary"], "native_operator": "UnsupportedNativeOp"}}
            for row in requests["requests"]
        ],
    }
    gap = predict_native_requests(unmodeled_requests, hardware=CONDITIONS["hardware"])
    assert gap["counts"]["status_unmodeled"] == 2
    assert all(row["reason"].startswith("t12_invocation_unavailable:")
               for row in gap["predictions"])
    report = compare_native_predictions(
        export_native_observations(CAPTURE, **CONDITIONS),
        gap["predictions"])
    assert report["counts"]["paired"] == 0
    assert report["counts"]["unpaired_observations"] == 2
    assert report["counts"]["unpaired_predictions"] == 2
    assert report["status"] == "inconclusive"


def test_sim_execution_known_null_and_conflict_sets(exported):
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report

    source = deepcopy(exported["observations"][0])
    source["conditions"]["execution"] = {"state_version": 1}
    observation_identity = _sim_identity(source)
    prediction_identity = {**observation_identity,
                           "execution": {"state_version": 1}}
    base = {
        "observations": [{
            "sample_id": source["observation_id"],
            "request_id": source["request_id"], "run_id": "r",
            "duration_ms": source["timing"]["duration_ms"],
            "identity": observation_identity, "source": source["source"],
            "split": "calibration", "metadata": {},
        }],
    }
    known = native_comparison_report({
        **base,
        "predictions": [{
            "prediction_id": "known", "request_id": source["request_id"],
            "duration_ms": source["timing"]["duration_ms"],
            "identity": prediction_identity,
        }],
    })
    assert known["coverage"]["paired"] == 1

    for name, value in (("null", None), ("conflict", {"state_version": 2})):
        report = native_comparison_report({
            **base,
            "predictions": [{
                "prediction_id": name, "request_id": source["request_id"],
                "duration_ms": source["timing"]["duration_ms"],
                "identity": {**observation_identity, "execution": value},
            }],
        })
        assert report["coverage"]["paired"] == 0
        assert report["not_comparable"][0]["reason"].startswith(
            "request_identity_conflict:")
        assert "execution" in report["not_comparable"][0]["reason"]
        assert report["not_comparable"][0]["observation_ids"] == [
            source["observation_id"]]


def test_t12_bridge_maps_explicit_api_plus_ordered_matmul_abi():
    pytest.importorskip("mindie_sim")
    from mindie_profiler.sim_bridge import predict_native_requests

    abi = native_abi_from_slots(
        "aclnnMatmul",
        [
            {"shape": [2048, 512], "dtype": "bf16", "layout": "ND"},
            {"shape": [512, 512], "dtype": "bf16", "layout": "ND"},
        ],
        [{"shape": [2048, 512], "dtype": "bf16", "layout": "ND"}],
    )
    request = {
        "request_id": "req:matmul-ordered",
        "api": {"namespace": "aclnn", "entry": "aclnnMatmul",
                "aclnn_symbol": "aclnnMatmul"},
        "version": {"api": "cann-9.2.0",
                    "image_id": "sha256:9e869e8148467296f56d1001b0dac4fea893c841ac7d0a03d4e824a233c2ffea"},
        "attrs": {},
        "conditions": {"variant": "dense_matmul",
                       "sequence_rows": "shard", "sequence_ranks": 2},
        "abi": abi,
    }
    result = predict_native_requests([request], hardware=CONDITIONS["hardware"])
    prediction = result["predictions"][0]
    assert prediction["status"] == "modeled"
    assert prediction["t12"]["binding"]["api"]["entry"] == "aclnnMatmul"
    assert prediction["abi"]["status"] == "complete"
    assert prediction["duration_ms"] > 0


def test_matmul_conditions_export_matches_direct_control():
    pytest.importorskip("mindie_sim")
    from mindie_profiler.sim_bridge import predict_native_requests

    invocation = {
        "api": {"namespace": "aclnn", "entry": "aclnnMatmul",
                "aclnn_symbol": "aclnnMatmul"},
        "version": {"api": "cann-9.2.0",
                    "image_id": "sha256:9e869e8148467296f56d1001b0dac4fea893c841ac7d0a03d4e824a233c2ffea"},
        "tensors": {
            "x1": {"shape": [2048, 512], "dtype": "bf16", "role": "input"},
            "x2": {"shape": [512, 512], "dtype": "bf16", "role": "weight"},
            "out": {"shape": [2048, 512], "dtype": "bf16", "role": "output"},
        },
        "attrs": {"epsilon": 1e-6},
        "conditions": {"variant": "dense_matmul",
                       "sequence_rows": "shard", "sequence_ranks": 2},
    }
    direct = predict_native_requests(
        [{"request_id": "req:add-export", "t12_invocation": invocation}],
        hardware=CONDITIONS["hardware"], phase="prefill")["predictions"][0]
    assert direct["status"] == "modeled"
    assert direct["duration_ms"] > 0

    conditions = {
        "hardware": CONDITIONS["hardware"], "phase": "prefill",
        "api": invocation["api"], "version": invocation["version"],
        "attrs": invocation["attrs"], "epsilon": 1e-6,
        "sequence_rows": "shard", "sequence_ranks": 2,
        "variant": "dense_matmul",
    }
    boundary = {"kind": "kernel", "native_operator": "aclnnMatmul",
                "scope": "one_complete_kernel_event",
                "expansion": "single_kernel_row", "fusion": {"members": []}}
    window = {"id": "window:add-export", "kind": "local_domain_range",
              "event_count": 1, "start_ns": 0, "end_ns": 1_000_000,
              "duration_ms": 1.0,
              "clock_comparable_across_domains": False}
    observation = {
        "observation_id": "observation:add-export",
        "request_id": "req:add-export", "boundary": boundary,
        "abi": direct["abi"], "conditions": conditions,
        "occurrence": {"rank": None, "device_id": "2", "stream_id": "7"},
        "clock": {"domain": "device:2:stream:7"},
        "timing": {"duration_ms": direct["duration_ms"],
                   "window_id": window["id"], "complete_in_window": True},
        "structure": {"status": "confirmed"}, "fusion": {"members": []},
    }
    observations = {
        "observations": [observation],
        "window": {"kind": "per_domain", "count": 1, "windows": [window]},
        "windows": [window],
        "counts": {"events": 1, "confirmed": 1, "candidate": 0,
                   "unidentified": 0, "requests": 1, "windows": 1,
                   "devices": 1, "missing_device_id": 0,
                   "missing_native_type": 0, "missing_stream_id": 0},
        "truncated": False,
    }
    requests = native_prediction_requests(observations)
    exported = predict_native_requests(
        requests, hardware=CONDITIONS["hardware"])["predictions"][0]
    assert exported["status"] == "modeled"
    assert exported["duration_ms"] == pytest.approx(direct["duration_ms"])
    assert exported["abi"]["digest"] == direct["abi"]["digest"]
    assert exported["t12"]["binding"]["call_id"] == (
        direct["t12"]["binding"]["call_id"])
    assert exported["condition_scope"]["sequence_ranks"] == "actual"
    assert exported["condition_scope"]["epsilon"] == "declaration"
    assert exported["t12"]["invocation"]["conditions"]["sequence_ranks"] == 2

    report = compare_native_predictions(
        observations, [exported], requests=requests)
    assert report["status"] == "passed"
    assert report["counts"]["paired"] == 1
    assert report["counts"]["within_tolerance"] == 1
    assert report["items"][0]["condition_gaps"] == []


def test_t12_r6_qbmm_actual_abi_is_work_only_paired():
    pytest.importorskip("mindie_sim")
    from mindie_profiler.sim_bridge import predict_native_requests

    observations = export_native_observations(
        CAPTURE, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"],
        model=CONDITIONS["model"], quant=CONDITIONS["quant"])
    requests = native_prediction_requests(observations)
    bridge = predict_native_requests(
        requests, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"],
        source_revision="r64")
    assert bridge["counts"]["status_modeled"] == 2
    for prediction, observation in zip(
            bridge["predictions"], observations["observations"]):
        assert prediction["status"] == "modeled"
        assert prediction["duration_ms"] > 0
        assert prediction["abi"]["status"] == "complete"
        assert prediction["abi"]["digest"]
        # The captured device ABI stores the weight as FRACTAL_NZ; the
        # normalized invocation exposes a logical ND view, so only an exact
        # digest agreement may certify a capture pairing.
        assert prediction["abi"]["digest"] != observation["abi"]["digest"]
        assert prediction["eligibility"]["capture_pairing"] is False
        assert prediction["work"]["cube"]["macs"] > 0

    report = compare_native_predictions(observations, bridge)
    # A normalized logical view is not the captured device ABI, so the
    # comparison reports the exact conflict instead of certifying a pairing.
    assert report["counts"]["paired"] == 0
    assert report["counts"]["predictions_with_abi_conflict"] == 2
    assert report["counts"]["unpaired_predictions"] == 2
    assert report["status"] == "inconclusive"
    assert all(item["reason"] == "request_identity_conflict:abi.digest"
               for item in report["unpaired_predictions"])

    no_source = predict_native_requests(
        requests, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    assert no_source["counts"]["status_modeled"] == 2
    assert all(row["status"] == "modeled" and row["duration_ms"] > 0
               for row in no_source["predictions"])


def test_native_directory_selection_preserves_clock_candidates(tmp_path):
    rank = tmp_path / "rank_0"
    rank.mkdir()
    shutil.copy(CAPTURE, rank / "kernel_details.csv")
    shutil.copy(CAPTURE, rank / "op_summary_a.csv")
    exported = export_native_observations(
        tmp_path, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    discovery = exported["source_discovery"]
    assert discovery["kind"] == "clock_inventory"
    assert discovery["rank_count"] == 1
    assert discovery["selected_path"] == str(rank / "kernel_details.csv")
    fact = discovery["ranks"][0]
    assert len(fact["csv_candidates"]) == 2
    assert any(path.endswith("op_summary_a.csv") for path in fact["csv_candidates"])
    assert discovery["sibling_rank_gaps"] == []
    assert any(row.get("clock", {}).get("domain")
               for row in fact["files"] if isinstance(row, dict))
    assert all("capture_id" in row for row in fact["files"] if isinstance(row, dict))


def test_native_directory_sibling_rank_without_abi_is_not_silently_dropped(tmp_path):
    for name in ("rank_0", "rank_1"):
        (tmp_path / name).mkdir()
    shutil.copy(CAPTURE, tmp_path / "rank_0" / "kernel_details.csv")
    shutil.copy(CAPTURE, tmp_path / "rank_1" / "op_summary_a.csv")
    with pytest.raises(ProfilerUsageError) as caught:
        export_native_observations(
            tmp_path, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    text = str(caught.value)
    assert "sibling rank has no kernel_details source" in text
    assert "rank_1" in text
    assert "op_summary_a.csv" in text

    selected = export_native_observations(
        tmp_path, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"],
        rank="0")
    assert selected["source_discovery"]["selected_rank"] == "rank_0"
    assert selected["source_discovery"]["sibling_rank_gaps"][0]["rank_id"] == "rank_1"


def test_native_directory_two_ranks_requires_explicit_rank(tmp_path):
    for name in ("rank_0", "rank_1"):
        (tmp_path / name).mkdir()
        shutil.copy(CAPTURE, tmp_path / name / "kernel_details.csv")
    with pytest.raises(ProfilerUsageError, match="multiple ranks have kernel_details"):
        export_native_observations(
            tmp_path, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"])
    selected = export_native_observations(
        tmp_path, hardware=CONDITIONS["hardware"], phase=CONDITIONS["phase"],
        rank="1")
    assert selected["source_discovery"]["selected_rank"] == "rank_1"
    assert selected["counts"]["events"] == 2


def test_actual_hardware_conflict_keeps_both_sides_unpaired(exported):
    source = deepcopy(exported["observations"][0])
    request = native_prediction_requests(exported)["requests"][0]
    prediction = {
        "prediction_id": "hardware-conflict", "request_id": request["request_id"],
        "duration_ms": source["timing"]["duration_ms"], "status": "modeled",
        "abi": source["abi"], "boundary": source["boundary"],
        "conditions": {
            **request["conditions"],
            "hardware": "Ascend910_9392",
        },
        "occurrence": source["occurrence"], "clock": source["clock"],
        "window_id": source["timing"]["window_id"],
    }
    observations = {"observations": [source], "window": exported["window"]}
    report = compare_native_predictions(observations, [prediction])
    assert report["counts"]["paired"] == 0
    assert report["counts"]["unpaired_observations"] == 1
    assert report["counts"]["unpaired_predictions"] == 1
    assert any("conditions.hardware" in conflict
               for conflict in report["unpaired_predictions"][0]["conflicts"])
    assert report["unpaired_observations"][0]["observed_ms"] == source["timing"]["duration_ms"]


def test_typed_attrs_participate_in_no_id_matching(exported):
    source = deepcopy(exported["observations"][0])
    source["conditions"]["attrs"] = {"epsilon": 1e-5}
    observations = {"observations": [source], "window": exported["window"]}
    prediction = {
        "prediction_id": "attrs-conflict", "duration_ms": source["timing"]["duration_ms"],
        "status": "modeled", "abi": source["abi"], "boundary": source["boundary"],
        "conditions": {"hardware": source["conditions"]["hardware"],
                       "attrs": {"epsilon": 1e-6}},
        "occurrence": source["occurrence"], "clock": source["clock"],
        "window_id": source["timing"]["window_id"],
    }
    report = compare_native_predictions(observations, [prediction])
    assert report["counts"]["paired"] == 0
    assert report["counts"]["unpaired_observations"] == 1
    assert report["counts"]["unpaired_predictions"] == 1


def test_t12_adapter_retains_top_level_and_conditions_api_conflict():
    from mindie_profiler.sim_bridge import _t12_invocation_from_request

    abi = native_abi_from_slots(
        "AddRmsNorm",
        [
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
            {"shape": [4], "dtype": "bf16", "layout": "ND"},
        ],
        [
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
            {"shape": [2, 1], "dtype": "fp32", "layout": "ND"},
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
        ],
    )
    request = {
        "request_id": "req:api-conflict",
        "api": {"namespace": "aclnn", "entry": "aclnnAddRmsNorm",
                "aclnn_symbol": "aclnnAddRmsNorm"},
        "conditions": {
            "api": {"namespace": "torch", "entry": "torch_npu.npu_rms_norm"},
            "hardware": CONDITIONS["hardware"],
        },
        "abi": abi,
        "attrs": {"epsilon": 1e-6},
    }
    invocation, gap, meta = _t12_invocation_from_request(request)
    assert gap is None
    assert any(row["field"].startswith("api.") for row in meta["conflicts"])
    assert invocation["api"]["entry"] == "aclnnAddRmsNorm"
    assert invocation["api"]["namespace"] == "aclnn"


def test_t12_adapter_does_not_fill_directory_version():
    from mindie_profiler.sim_bridge import _t12_invocation_from_request

    abi = native_abi_from_slots(
        "AddRmsNorm",
        [
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
            {"shape": [4], "dtype": "bf16", "layout": "ND"},
        ],
        [
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
            {"shape": [2, 1], "dtype": "fp32", "layout": "ND"},
            {"shape": [2, 4], "dtype": "bf16", "layout": "ND"},
        ],
    )
    request = {
        "api": {"namespace": "aclnn", "entry": "aclnnAddRmsNorm"},
        "abi": abi,
        "attrs": {"epsilon": 1e-6},
    }
    invocation, gap, meta = _t12_invocation_from_request(request)
    assert gap is None
    assert invocation["version"] == {}


def test_filtered_top_windows_cannot_shrink_original_counts(exported):
    tail = deepcopy(exported)
    tail["observations"] = [
        row for row in exported["observations"]
        if row["timing"]["duration_ms"] < 0.1]
    tail_window = tail["observations"][0]["timing"]["window_id"]
    tail["windows"] = [row for row in exported["windows"] if row["id"] == tail_window]
    assert tail["counts"]["events"] == 2
    request = native_prediction_requests(tail)["requests"][0]
    prediction = {
        "prediction_id": "tail-only", "request_id": request["request_id"],
        "duration_ms": tail["observations"][0]["timing"]["duration_ms"],
        "status": "modeled", "abi": tail["observations"][0]["abi"],
        "boundary": tail["observations"][0]["boundary"],
        "conditions": tail["observations"][0]["conditions"],
        "occurrence": tail["observations"][0]["occurrence"],
        "clock": tail["observations"][0]["clock"],
        "window_id": tail_window,
    }
    report = compare_native_predictions(tail, [prediction], requests=[request])
    assert report["items"][0]["status"] == "within_tolerance"
    assert report["status"] == "partial"
    assert report["coverage"]["reconciliation"]["counts_events"] == 2
    assert report["coverage"]["reconciliation"]["missing_events"] == 1

    stripped = deepcopy(tail)
    stripped["window"].pop("windows", None)
    report = compare_native_predictions(stripped, [prediction], requests=[request])
    assert report["status"] == "partial"
    assert report["coverage"]["reconciliation"]["declaration_conflicts"]

    scoped = deepcopy(tail)
    scoped["scope"] = {"window_ids": [tail_window], "event_count": 1,
                       "parent_capture_id": "capture:parent"}
    report = compare_native_predictions(scoped, [prediction], requests=[request])
    assert report["status"] == "passed"
    assert report["coverage"]["reconciliation"]["parent_remaining_events"] == 1


def test_equivalent_undefined_slots_share_identity_and_keep_raw():
    pytest.importorskip("mindie_sim")
    if T03_FIRST_CALL.is_file():
        record = json.loads(T03_FIRST_CALL.read_text())
    else:
        record = {
            "native_operator_type": "CausalConv1d",
            "raw_abi": {
                "inputs": [
                    {"shape": [384, 5120], "dtype": "bf16", "layout": "ND"},
                    {"shape": [4, 5120], "dtype": "bf16", "layout": "ND"},
                    {"shape": [], "dtype": None, "layout": None},
                    {"shape": [2188, 6, 5120], "dtype": "bf16", "layout": "ND"},
                    {"shape": [97], "dtype": "int32", "layout": "ND"},
                    {"shape": [96], "dtype": "int32", "layout": "ND"},
                    {"shape": [], "dtype": None, "layout": None},
                    {"shape": [96], "dtype": "int32", "layout": "ND"},
                    {"shape": [], "dtype": None, "layout": None},
                    {"shape": [], "dtype": None, "layout": None},
                    {"shape": [], "dtype": None, "layout": None},
                    {"shape": [], "dtype": None, "layout": None},
                ],
                "outputs": [
                    {"shape": [384, 5120], "dtype": "bf16", "layout": "ND"},
                ],
            },
        }
    raw = record.get("raw_abi") or {}
    inputs = [dict(item) for item in raw.get("inputs") or ()]
    outputs = [dict(item) for item in raw.get("outputs") or ()]
    index = next(i for i, item in enumerate(inputs)
                 if item.get("dtype") is None and item.get("layout") is None)
    normalized = native_abi_from_slots(record.get("native_operator_type"), inputs, outputs)
    raw_inputs = deepcopy(inputs)
    raw_inputs[index]["dtype"] = "DT_UNDEFINED"
    raw_inputs[index]["layout"] = "NULL"
    raw_abi = native_abi_from_slots(record.get("native_operator_type"), raw_inputs, outputs)
    assert normalized["status"] == raw_abi["status"] == "complete"
    assert normalized["digest"] == raw_abi["digest"]
    assert len(normalized["inputs"]) == len(raw_abi["inputs"]) == 12
    assert raw_abi["inputs"][index]["dtype_raw"] == "DT_UNDEFINED"
    assert raw_abi["inputs"][index]["layout_raw"] == "NULL"


def test_t12_abi_keeps_absent_declared_position():
    from types import SimpleNamespace
    from mindie_profiler.sim_bridge import _t12_abi

    result = SimpleNamespace(
        invocation={"tensors": {
            "a": {"shape": [2, 4], "dtype": "bf16", "layout": "ND", "present": True},
            "absent": {"shape": None, "dtype": None, "layout": None,
                       "present": False, "optional": False},
            "b": {"shape": [2, 4], "dtype": "bf16", "layout": "ND", "present": True},
            "out": {"shape": [2, 4], "dtype": "bf16", "layout": "ND",
                    "role": "output", "present": True},
        }},
        program={"physical": {"tensors": {
            "a": {"shape": [2, 4], "dtype": "bf16", "layout": "ND", "role": "input"},
            "b": {"shape": [2, 4], "dtype": "bf16", "layout": "ND", "role": "input"},
            "out": {"shape": [2, 4], "dtype": "bf16", "layout": "ND", "role": "output"},
        }}},
        binding=SimpleNamespace(to_dict=lambda: {
            "kernels": [{"name": "SyntheticAbsent"}],
            "typed": {},
        }),
        spec={"entry": "SyntheticAbsent"},
    )
    abi = _t12_abi(result)
    assert abi["status"] == "complete"
    assert len(abi["inputs"]) == 3
    assert abi["inputs"][1]["present"] is False


T18_CHAIN = Path(os.environ.get(
    "MINDIE_T18_CHAIN",
    "capture://codex/2026-11-12/kan-x/work/a5-implementation/jobs/"
    "A5-T18/logs/t16-chain"))


def test_t18_w8a8_wave8_chain_and_call_id():
    requests_path = T18_CHAIN / "requests.json"
    observations_path = T18_CHAIN / "observations.json"
    if not requests_path.is_file() or not observations_path.is_file():
        pytest.skip("T18 wave8 requests/observations unavailable")
    requests = json.loads(requests_path.read_text())["requests"]
    observations = json.loads(observations_path.read_text())
    no_version = predict_native_requests(
        requests, hardware=CONDITIONS["hardware"], phase="decode")
    assert no_version["counts"]["status_modeled"] == 2
    for row in no_version["predictions"]:
        assert row["duration_ms"] > 0
        assert row["t12"]["binding_bound"] is False
        assert "attributable_source_reference_unresolved" in (
            row["t12"]["binding"]["unresolved"])

    versioned = [{**row, "version": {"source": "r31"}} for row in requests]
    executed = predict_native_requests(
        versioned, hardware=CONDITIONS["hardware"], phase="decode")
    assert executed["counts"]["status_modeled"] == 2
    for row in executed["predictions"]:
        assert row["duration_ms"] > 0
        assert row["t12"]["binding_bound"] is True

    bridge = predict_native_requests(
        versioned, hardware=CONDITIONS["hardware"], phase="decode",
        execute=False)
    assert bridge["counts"]["status_modeled_work_only"] == 2
    call_ids = {row["t12"]["binding"]["call_id"] for row in bridge["predictions"]}
    assert len(call_ids) == 1
    for row in bridge["predictions"]:
        assert row["abi"]["digest"] == (
            "sha256:5f8d76f452c9720a2822fc9690a808d6719b97bbfdb3c42f56e6cd15fe7823e8")
        assert row["duration_ms"] is None
        assert row["t12"]["binding_bound"] is True
        assert row["work"]["bytes"]["weight_scale"] == 10240
        assert row["work"]["bytes"]["pertoken_scale"] == 16
        assert row["work"]["bytes"]["output"] == 40960
        assert row["work"]["bytes"]["total"] == 44650512
    conflicting = predict_native_requests(
        [{**requests[0], "version": {"source": "r31",
                                     "image_id": "sha256:" + "a" * 64}}],
        hardware=CONDITIONS["hardware"], phase="decode")["predictions"][0]
    assert conflicting["status"] == "unmodeled"
    assert "version:image_not_r31" in conflicting["reason"]

    report = compare_native_predictions(observations, bridge)
    assert report["status"] == "inconclusive"
    assert report["counts"]["paired"] == 2
    assert report["counts"]["work_only"] == 2
    assert report["counts"]["unpaired_observations"] == 0
    assert report["counts"]["unpaired_predictions"] == 0

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        obs_path, pred_path = root / "obs.json", root / "pred.json"
        out_path = root / "out.json"
        obs_path.write_text(json.dumps(observations))
        pred_path.write_text(json.dumps({"predictions": bridge["predictions"]}))
        code = main(["--native-observations", str(obs_path),
                     "--predictions", str(pred_path),
                     "--output", str(out_path)])
        assert code == 3
        assert json.loads(out_path.read_text())["status"] == "inconclusive"


def test_t18_explicit_r31_invocation_matches_top_level_version():
    requests_path = T18_CHAIN / "requests.json"
    if not requests_path.is_file():
        pytest.skip("T18 wave8 requests unavailable")
    pytest.importorskip("mindie_sim")
    from mindie_profiler.sim_bridge_case import _qbmm_w8a8_invocation

    requests = json.loads(requests_path.read_text())["requests"]
    versioned = [{**row, "version": {"source": "r31"}} for row in requests]
    top_executed = predict_native_requests(
        versioned, hardware=CONDITIONS["hardware"], phase="decode")
    assert top_executed["counts"]["status_modeled"] == 2
    assert all(row["duration_ms"] > 0 and row["t12"]["binding_bound"] is True
               for row in top_executed["predictions"])

    top_level = predict_native_requests(
        versioned, hardware=CONDITIONS["hardware"], phase="decode",
        execute=False)
    assert top_level["counts"]["status_modeled_work_only"] == 2

    explicit = []
    for row in requests:
        invocation = _qbmm_w8a8_invocation(
            row["abi"], version={"source": "r31"},
            conditions=row["conditions"])
        explicit.append({**row, "t12_invocation": invocation})
    explicit_executed = predict_native_requests(
        explicit, hardware=CONDITIONS["hardware"], phase="decode")
    assert explicit_executed["counts"]["status_modeled"] == 2
    assert ({row["t12"]["binding"]["call_id"]
             for row in top_executed["predictions"]}
            == {row["t12"]["binding"]["call_id"]
                for row in explicit_executed["predictions"]})

    bridge = predict_native_requests(
        explicit, hardware=CONDITIONS["hardware"], phase="decode",
        execute=False)
    assert bridge["counts"]["status_modeled_work_only"] == 2
    top_ids = {row["t12"]["binding"]["call_id"]
               for row in top_level["predictions"]}
    explicit_ids = {row["t12"]["binding"]["call_id"]
                    for row in bridge["predictions"]}
    assert top_ids == explicit_ids
    assert len(explicit_ids) == 1
    for row in bridge["predictions"]:
        assert row["duration_ms"] is None
        assert row["work"]["bytes"]["total"] == 44650512
        assert row["t12"]["invocation"]["version"]["source"] == "r31"
        assert row["condition_scope"]["phase"] == "actual"
        assert row["conditions"]["phase"] == "decode"


def _seq_boundary():
    return {"kind": "kernel", "native_operator": "aclnnMatmul",
            "scope": "one_complete_kernel_event",
            "expansion": "single_kernel_row", "fusion": {"members": []}}


def _matmul_prediction(sequence_ranks, *, request_conditions=None):
    invocation = {
        "api": {"namespace": "aclnn", "entry": "aclnnMatmul",
                "aclnn_symbol": "aclnnMatmul"},
        "version": {"api": "cann-9.2.0",
                    "image_id": "sha256:9e869e8148467296f56d1001b0dac4fea893c841ac7d0a03d4e824a233c2ffea"},
        "tensors": {
            "x1": {"shape": [2, 4], "dtype": "bf16", "role": "input"},
            "x2": {"shape": [4, 8], "dtype": "bf16", "role": "weight"},
            "out": {"shape": [2, 8], "dtype": "bf16", "role": "output"},
        },
        "attrs": {"epsilon": 1e-6},
        "conditions": {"variant": "fused_attention_norm",
                       "sequence_rows": "shard",
                       "sequence_ranks": sequence_ranks},
    }
    request = {
        "request_id": "req:seq", "t12_invocation": invocation,
        "boundary": _seq_boundary(),
        "occurrence": {"rank": None, "device_id": "2", "stream_id": "7"},
        "clock": {"domain": "rank:/device:2/stream:7"},
        "window_id": "window:seq",
    }
    if request_conditions is None:
        request_conditions = {"sequence_ranks": 1}
    if request_conditions:
        request["conditions"] = dict(request_conditions)
    return predict_native_requests(
        [request], hardware=CONDITIONS["hardware"],
        phase="prefill")["predictions"][0]


def _seq_inputs(prediction, *, observation_request_id="req:seq",
                prediction_request_id="req:seq"):
    observation = {
        "observation_id": "observation:seq",
        "boundary": _seq_boundary(), "abi": prediction["abi"],
        "conditions": {
            **prediction["conditions"],
            "hardware": CONDITIONS["hardware"], "phase": "prefill",
            "sequence_ranks": 1,
        },
        "occurrence": {"rank": None, "device_id": "2", "stream_id": "7"},
        "clock": {"domain": "rank:/device:2/stream:7"},
        "timing": {"duration_ms": prediction["duration_ms"],
                   "window_id": "window:seq"},
        "structure": {"status": "confirmed"},
        "fusion": {"members": []},
    }
    payload = deepcopy(prediction)
    if observation_request_id is not None:
        observation["request_id"] = observation_request_id
    if prediction_request_id is not None:
        payload["request_id"] = prediction_request_id
    else:
        payload.pop("request_id", None)
    request = {
        "request_id": observation_request_id, "boundary": _seq_boundary(),
        "abi": prediction["abi"], "conditions": observation["conditions"],
        "occurrence": observation["occurrence"], "clock": observation["clock"],
        "timing": {"window_id": "window:seq"},
    }
    return {"observations": [observation],
            "window": {"kind": "per_domain"}}, [payload], request


def _seq_report(prediction, *, with_request, observation_request_id="req:seq",
                prediction_request_id="req:seq"):
    observations, predictions, request = _seq_inputs(
        prediction, observation_request_id=observation_request_id,
        prediction_request_id=prediction_request_id)
    return compare_native_predictions(
        observations, predictions,
        requests=[request] if with_request else None)


def test_actual_sequence_ranks_conflict_same_and_no_id():
    conflicting = _matmul_prediction(2, request_conditions={})
    assert conflicting["conditions"]["sequence_ranks"] == 2
    same_id = _seq_report(conflicting, with_request=True)
    assert same_id["counts"]["paired"] == 0
    assert same_id["counts"]["unpaired_observations"] == 1
    assert same_id["counts"]["unpaired_predictions"] == 1
    assert same_id["status"] == "inconclusive"
    assert "sequence_ranks" in same_id["unpaired_observations"][0]["reason"]

    no_id = _seq_report(
        conflicting, with_request=False, observation_request_id=None,
        prediction_request_id=None)
    assert no_id["counts"]["paired"] == 0
    assert no_id["counts"]["unpaired_observations"] == 1
    assert no_id["counts"]["unpaired_predictions"] == 1
    assert no_id["counts"]["observation_verdicts"] == 0
    assert no_id["status"] == "inconclusive"
    assert "sequence_ranks" in no_id["unpaired_observations"][0]["reason"]
    assert "sequence_ranks" in no_id["unpaired_predictions"][0]["reason"]
    assert no_id["unpaired_predictions"][0]["identity_differences"]

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        observations, predictions, _ = _seq_inputs(
            conflicting, observation_request_id=None,
            prediction_request_id=None)
        obs_path, pred_path, out_path = (root / "obs.json",
                                         root / "pred.json", root / "out.json")
        obs_path.write_text(json.dumps(observations))
        pred_path.write_text(json.dumps({"predictions": predictions}))
        code = main(["--native-observations", str(obs_path),
                     "--predictions", str(pred_path),
                     "--output", str(out_path)])
        assert code == 3
        assert json.loads(out_path.read_text())["status"] == "inconclusive"

    missing = deepcopy(conflicting)
    missing["conditions"].pop("sequence_ranks", None)
    missing["condition_conflicts"] = []
    missing_report = _seq_report(missing, with_request=True)
    assert missing_report["counts"]["paired"] == 0
    assert missing_report["unpaired_predictions"][0]["reason"].startswith(
        "condition_missing:sequence_ranks:")

    consumed = deepcopy(missing)
    consumed["condition_consumption"] = {
        "sequence_ranks": {
            "value": 1, "evidence": ["t12.invocation.conditions"],
        },
    }
    consumed_report = _seq_report(consumed, with_request=True)
    assert consumed_report["counts"]["paired"] == 1
    assert consumed_report["items"][0]["comparison"]["within_tolerance"] is True

    matching = _matmul_prediction(1)
    report = _seq_report(matching, with_request=True)
    assert report["counts"]["paired"] == 1
    assert report["items"][0]["comparison"]["within_tolerance"] is True


def test_sim_sequence_conflict_preserves_identity_and_values(exported):
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report

    source = exported["observations"][0]
    observation_identity = _sim_identity(source)
    observation_identity["conditions"] = {
        **observation_identity["conditions"], "sequence_ranks": 1,
    }
    prediction_identity = {
        **observation_identity,
        "conditions": {
            **observation_identity["conditions"], "sequence_ranks": 2,
        },
    }
    observed_ms = source["timing"]["duration_ms"]
    report = native_comparison_report({
        "observations": [{
            "sample_id": source["observation_id"],
            "request_id": source["request_id"], "run_id": "r",
            "duration_ms": observed_ms,
            "identity": observation_identity, "source": source["source"],
            "split": "calibration", "metadata": {},
        }],
        "predictions": [{
            "prediction_id": "sequence-conflict",
            "request_id": source["request_id"],
            "duration_ms": observed_ms,
            "identity": prediction_identity,
        }],
    })
    assert report["status"] == "partial"
    assert report["coverage"]["paired"] == 0
    assert report["not_comparable"][0]["reason"] == (
        "request_identity_conflict:sequence_ranks")
    assert report["not_comparable"][0]["observation_ids"] == [
        source["observation_id"]]
    assert report["not_comparable"][0]["observed_ms"] == observed_ms
    assert report["not_comparable"][0]["identity"]["conditions"][
        "sequence_ranks"] == 1
    assert report["unpaired_predictions"][0]["prediction_id"] == (
        "sequence-conflict")
    assert report["unpaired_predictions"][0]["predicted_ms"] == observed_ms
    assert report["unpaired_predictions"][0]["identity"]["conditions"][
        "sequence_ranks"] == 2


def test_same_request_id_different_sequence_is_not_deduplicated(exported):
    first = deepcopy(exported["observations"][0])
    second = deepcopy(first)
    first["request_id"] = second["request_id"] = "req:dedupe-sequence"
    first["observation_id"] = "observation:dedupe-1"
    second["observation_id"] = "observation:dedupe-2"
    first["conditions"] = {**first["conditions"], "sequence_ranks": 1}
    second["conditions"] = {**second["conditions"], "sequence_ranks": 2}
    with pytest.raises(ProfilerUsageError,
                       match="conflicting native request identity"):
        native_prediction_requests({"observations": [first, second]})

    requests = []
    for observation in (first, second):
        requests.append({
            "request_id": observation["request_id"],
            "boundary": observation["boundary"], "abi": observation["abi"],
            "conditions": observation["conditions"],
            "occurrence": observation["occurrence"],
            "clock": observation["clock"],
            "window_id": observation["timing"]["window_id"],
        })
    prediction = {
        "prediction_id": "dedupe-prediction",
        "request_id": "req:dedupe-sequence",
        "duration_ms": first["timing"]["duration_ms"],
        "status": "modeled", "abi": first["abi"],
    }
    report = compare_native_predictions(
        {"observations": [first, second]}, [prediction], requests=requests)
    assert report["counts"]["paired"] == 0
    assert report["counts"]["request_groups"] == 1
    assert report["counts"]["unpaired_observations"] == 1
    assert "sequence_ranks" in report["unpaired_observations"][0]["reason"]


def test_sim_same_id_epsilon_conflict_is_partial(exported):
    pytest.importorskip("mindie_sim")
    from mindie_sim.observations.comparison import native_comparison_report

    source = exported["observations"][0]
    observation_identity = {**_sim_identity(source),
                            "attrs": {"epsilon": 1e-6}}
    prediction_identity = {**observation_identity,
                           "attrs": {"epsilon": 1e-5}}
    report = native_comparison_report({
        "observations": [{
            "sample_id": source["observation_id"],
            "request_id": source["request_id"], "run_id": "r",
            "duration_ms": source["timing"]["duration_ms"],
            "identity": observation_identity, "source": source["source"],
            "split": "calibration", "metadata": {},
        }],
        "predictions": [{
            "prediction_id": "epsilon-conflict",
            "request_id": source["request_id"],
            "duration_ms": source["timing"]["duration_ms"],
            "identity": prediction_identity,
        }],
    })
    assert report["coverage"]["paired"] == 0
    assert report["status"] == "partial"
    assert report["not_comparable"][0]["reason"] == "request_identity_conflict:attrs"
    assert report["unpaired_predictions"][0]["prediction_id"] == "epsilon-conflict"


def test_w8a8_nd_quant_does_not_map_to_weight_nz():
    abi = native_abi_from_slots(
        "QuantBatchMatmulV3",
        [
            {"shape": [4, 8704], "dtype": "int8", "layout": "ND"},
            {"shape": [8704, 5120], "dtype": "int8", "layout": "ND"},
            {"shape": [5120], "dtype": "bf16", "layout": "ND"},
            {"shape": [4], "dtype": "fp32", "layout": "ND"},
        ],
        [{"shape": [4, 5120], "dtype": "bf16", "layout": "ND"}],
    )
    request = {
        "request_id": "nd-quant",
        "boundary": {"kind": "kernel", "native_operator": "QuantBatchMatmulV3",
                     "scope": "one_complete_kernel_event",
                     "expansion": "single_kernel_row"},
        "abi": abi, "version": {"source": "r31"},
        "api": {"namespace": "torch",
                "entry": "torch_npu.npu_quant_matmul"},
        "conditions": {"phase": "decode", "hardware": CONDITIONS["hardware"]},
        "occurrence": {}, "clock": {}, "window_id": "window:nd",
    }
    prediction = predict_native_requests(
        [request], hardware=CONDITIONS["hardware"], phase="decode")["predictions"][0]
    assert prediction["status"] == "modeled"
    shapes = prediction["t12"]["binding"]["typed"]["shapes"]
    assert "weight" in shapes and "weight_nz" not in shapes
    assert prediction["t12"]["invocation"]["api"]["namespace"] == "torch"
    assert prediction["t12"]["invocation"]["api"]["entry"] == (
        "torch_npu.npu_quant_matmul")
    assert prediction["abi"]["status"] == "complete"
    assert prediction["abi"]["digest"] == abi["digest"]


def test_w8a8_aclnn_weight_nz_keeps_declared_api_and_representation():
    pytest.importorskip("mindie_sim")
    abi = native_abi_from_slots(
        "QuantBatchMatmulV3",
        [
            {"shape": [4, 8704], "dtype": "int8", "layout": "ND"},
            {"shape": [160, 544, 16, 32], "dtype": "int8",
             "layout": "FRACTAL_NZ"},
            {"shape": [5120], "dtype": "bf16", "layout": "ND"},
            {"shape": [4], "dtype": "fp32", "layout": "ND"},
        ],
        [{"shape": [4, 5120], "dtype": "bf16", "layout": "ND"}],
    )
    request = {
        "request_id": "aclnn-nz",
        "boundary": {"kind": "kernel", "native_operator": "QuantBatchMatmulV3",
                     "scope": "one_complete_kernel_event",
                     "expansion": "single_kernel_row"},
        "abi": abi, "version": {"source": "r31"},
        "api": {"namespace": "aclnn",
                "entry": "aclnnQuantMatmulWeightNz",
                "aclnn_symbol": "aclnnQuantMatmulWeightNz"},
        "conditions": {"phase": "decode", "hardware": CONDITIONS["hardware"]},
        "occurrence": {}, "clock": {}, "window_id": "window:aclnn-nz",
    }
    prediction = predict_native_requests(
        [request], hardware=CONDITIONS["hardware"],
        phase="decode")["predictions"][0]
    # FRACTAL_NZ is not a normalized ND matrix operand, so the storage view is
    # an explicit geometry gap instead of a guessed [k, n] MAC count.
    assert prediction["status"] == "unmodeled"
    assert prediction["reason"] == (
        "t12_invocation_unavailable:gemm_geometry_incomplete")

    nd_abi = native_abi_from_slots(
        "QuantBatchMatmulV3",
        [
            {"shape": [4, 8704], "dtype": "int8", "layout": "ND"},
            {"shape": [8704, 5120], "dtype": "int8", "layout": "ND"},
            {"shape": [5120], "dtype": "bf16", "layout": "ND"},
            {"shape": [4], "dtype": "fp32", "layout": "ND"},
        ],
        [{"shape": [4, 5120], "dtype": "bf16", "layout": "ND"}],
    )
    modeled = predict_native_requests(
        [{**request, "request_id": "aclnn-nd", "abi": nd_abi}],
        hardware=CONDITIONS["hardware"], phase="decode")["predictions"][0]
    assert modeled["status"] == "modeled"
    assert modeled["t12"]["invocation"]["api"]["entry"] == (
        "aclnnQuantMatmulWeightNz")
    shapes = modeled["t12"]["binding"]["typed"]["shapes"]
    assert shapes["weight"] == [8704, 5120]
    assert "weight_nz" not in shapes


def test_source_domains_keep_runner_and_binary_separate():
    abi = native_abi_from_slots(
        "QuantBatchMatmulV3",
        [
            {"shape": [4, 8704], "dtype": "int8", "layout": "ND"},
            {"shape": [8704, 5120], "dtype": "int8", "layout": "ND"},
            {"shape": [5120], "dtype": "bf16", "layout": "ND"},
            {"shape": [4], "dtype": "fp32", "layout": "ND"},
        ],
        [{"shape": [4, 5120], "dtype": "bf16", "layout": "ND"}],
    )
    request = {
        "request_id": "source-domains",
        "boundary": {"kind": "kernel", "native_operator": "QuantBatchMatmulV3",
                     "scope": "one_complete_kernel_event",
                     "expansion": "single_kernel_row"},
        "abi": abi,
        "version": {"api": "cann-9.2.0"},
        "software": {"torch": "2.6", "torch_npu": "2.6.0", "cann": "9.2.0"},
        "runner_source": {"vllm_commit": "deadbeef"},
        "conditions": {"phase": "decode", "hardware": CONDITIONS["hardware"]},
        "occurrence": {}, "clock": {}, "window_id": "window:source",
    }
    prediction = predict_native_requests(
        [request], hardware=CONDITIONS["hardware"], phase="decode")["predictions"][0]
    domains = prediction["source_domains"]
    assert domains["request_software"]["torch"] == "2.6"
    assert domains["runner_source"]["vllm_commit"] == "deadbeef"
    assert domains["t12_invocation_version"]["api"] == "cann-9.2.0"
    # No canonical source-binding receipt exists for a generic OpSpec call.
    assert domains["t12_binding_source"] is None
    assert prediction["eligibility"]["timed_pairing"] is True
    assert prediction["eligibility"]["cpu_mechanism"] is True
    assert prediction["eligibility"]["selected_plan"] is True
