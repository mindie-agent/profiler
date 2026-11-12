"""Declared producer supply, unknown A2, and a four-frame Qwen engine check.

The ordinary publisher prices every true frame. This module's engine check
names four declared indexes and does not run the other 135.

The host fleet table is an opt-in archive integration. Set
``MINDIE_ARCHIVE_INTEGRATION=1`` or pass ``-m archive_integration``.
``MINDIE_FLEET_CAPTURES`` selects the jsonl. A missing file skips; it does
not fail the ordinary suite.
"""
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

import fleet_archive_case as archive_case  # noqa: E402
import fleet_capture_observations as observations  # noqa: E402
import fleet_operator_archive as archive  # noqa: E402
import fleet_operator_archive_engine as engine  # noqa: E402
import fleet_operator_modeling as modeling  # noqa: E402
import hf_benchmark_gate as gate  # noqa: E402
import hf_sample_scoring as scoring  # noqa: E402
import mindie_sim.prediction.body as body  # noqa: E402
from mindie_sim.prediction.operator_analysis import target_graphs  # noqa: E402
from mindie_sim.prediction.structure import parse_case  # noqa: E402

def _jsonl() -> Path:
    override = os.environ.get("MINDIE_FLEET_CAPTURES", "")
    if override:
        return Path(override)
    return Path("/tmp/mindie-sim-profiling-bench/data/fleet_captures.jsonl")


def _archive_requested(config: pytest.Config) -> bool:
    if os.environ.get("MINDIE_ARCHIVE_INTEGRATION") == "1":
        return True
    return "archive_integration" in str(config.option.markexpr or "")


JSONL = _jsonl()
MC2_TP_CALLER = {
    "kind": "vllm_ascend_mc2_tp_slice",
    "padding": "right_to_tp",
    "padding_implementation": "concat",
    "gather_output_materialization": "view",
    "logits_dtype": "float32",
    "layer_scopes": ["body"],
}
A2 = "wave5:a2:a2/a2_real_dsv2lite_E64_K6_tp4ep4_prefill:a2_real_dsv2lite_E64_K6_tp4ep4_prefill_4k_c1"
QWEN = "wave5:a5:a5/a5_qwen30ba3b_tp4_ep4_decode:a5_qwen30ba3b_tp4_ep4_decode_4k_c1"
KIMI = "dsh_heldout:a3/heldout_engine_20261030/kimi_k3_w4a8_4layer_tp16_ep16_heldout_20261030/prof/prefill_c1_p16k/kernel_details.csv"
TEMPLATE_PRICE = 94.80180157034263
MATERIAL = (0, 1, 2, 138)


pytestmark = pytest.mark.archive_integration


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pytestconfig: pytest.Config) -> None:
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    if not _archive_requested(pytestconfig):
        pytest.skip("archive integration is opt-in")
    if not JSONL.is_file():
        pytest.skip(f"host fleet archive absent: {JSONL}")


def _rows() -> dict[str, dict]:
    if not JSONL.is_file():
        pytest.skip(f"host fleet archive absent: {JSONL}")
    found = {}
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("capture_id") in {A2, QWEN, KIMI}:
            found[row["capture_id"]] = row
    return found


def _resolve(row: dict) -> dict:
    archive_case.configure_archive_roots(receipt_index=None)
    resolved = archive_case.resolve_archive_case(row)
    assert isinstance(resolved, dict)
    return resolved


def _window(keys: list[str], phase: str, *, capture_id: str, hardware_tier: str, source_sha: str = "") -> dict:
    observation = {
        "capture": {"capture_id": capture_id, "phase": phase, "hardware_tier": hardware_tier},
        "source": {"path": "/obs/kernel_details.csv"},
        "measurements": {"per_forward_window": {
            "status": "measured",
            "samples_basis": "elapsed",
            "samples": [{"key": key, "observed_ms": 10.0, "phase": phase} for key in keys],
        }},
    }
    if source_sha:
        observation["source"]["sha256"] = source_sha
    return observation


def test_declaration_join_keeps_frames_and_the_applied_sku(monkeypatch: pytest.MonkeyPatch) -> None:
    """Producer frames stay the schedule. The applied PR sku is not blanked."""
    def _forbidden(*_args, **_kwargs):
        raise AssertionError("body_forward during declaration join")

    monkeypatch.setattr(body, "body_forward", _forbidden)
    modeling.clear_caches()
    source = Path(archive.__file__).read_text(encoding="utf-8")
    assert "_INLINE_PRICE_FRAMES" not in source
    assert "exact_score_withheld_until_physical_substrate" not in source
    rows = _rows()
    assert set(rows) == {A2, QWEN, KIMI}
    a2 = modeling._archive_probe(_resolve(rows[A2]))
    qwen_resolved = _resolve(rows[QWEN])
    poisoned = json.loads(json.dumps(qwen_resolved))
    poisoned["observed_ms"] = 1
    poisoned["predicted_ms"] = 2
    poisoned["kernel_summary"] = {"poison": True}
    poisoned["structural_weights"] = [0.5]
    qwen = modeling._archive_probe(qwen_resolved)
    qwen_poison = modeling._archive_probe(poisoned)
    kimi = modeling._archive_probe(_resolve(rows[KIMI]))

    assert a2["ok"] is True and a2["exact"] is False and a2["single_sku_case"] is False
    assert a2["supply_kind"] == "unknown" and a2["sku"] == ""
    assert a2["hardware_selection"] == "not_selected"
    assert len(a2["frames"]) == 1 and a2["chunk_steps"] == [(4096, 0, 1)]
    assert a2["context_source"] == "producer_geometry_frames"
    assert a2["observed_cached_tokens"] == 0 and a2["designed_prefix_tokens"] is None
    assert a2["deployment_dp"] == 1 and a2["deployment_dp_per_window"] is False
    assert a2["frames"][0]["forward_id"] == "prefill:0"
    assert a2["frames"][0]["chunk_forward_id"] == 0
    assert a2["frames"][0]["device_id"] == "4"
    assert a2["frames"][0]["receipt_rank_id"] == "" and a2["frames"][0]["rank_id"] is None
    assert "dp" not in a2["frames"][0]
    assert a2["needed"] == ["catalogue sku for declared identity Ascend910B_A2"]
    assert a2["needed_by_id"] == {"phase=prefill|device_id=4|forward_id=prefill:0": a2["needed"]}
    assert a2["ambiguous"]["unmapped_identities"] == ["Ascend910B_A2"]
    assert a2["ambiguous"]["audit_candidates"] == [
        {"catalog_sku": "Ascend910B4", "role": "template_subtype_not_measurement", "applied": False},
    ]
    assert [item["catalog_sku"] for item in a2["hardware_candidates"]] == [None, "Ascend910B4"]
    assert all(item["priced"] is False and item["selected"] is False and item["exact"] is False for item in a2["hardware_candidates"])
    assert a2["hardware_candidates"][0]["reason"] == "declared_identity_has_no_catalog_sku"
    assert a2["hardware_candidates"][1]["supply"] is False
    assert "equipment proof" not in " ".join(a2["needed"])
    assert "Ascend910B4" not in " ".join(a2["needed"])
    assert "producer_frames_are_the_step_schedule" in a2["diagnostics"]
    assert "hardware_supply_not_concrete" in a2["diagnostics"]
    assert "exact_score_withheld_until_physical_substrate" not in a2["diagnostics"]
    by_source = {(item["source"], item["tokens"]) for item in a2["designed_prefix_by_source"]}
    assert ("usage.design.shared_tokens", 4088) in by_source or ("cellset.design.shared_tokens", 4088) in by_source
    assert ("meta.env:PREFIX_LEN", 0) in by_source
    assert ("run_meta.workload.prefix_len", 0) in by_source

    assert qwen["supply_kind"] == "declared_producer_sku"
    assert qwen["sku"] == "Ascend950PR_9579" and qwen["case"]["machine"]["sku"] == "Ascend950PR_9579"
    qwen_model = qwen["case"]["model"]
    assert qwen_model["moe_intermediate_size"] == 768 and qwen_model["ffn"] == "moe"
    assert qwen_model["intermediate_size"] == 768
    assert qwen["exact"] is False and qwen["hardware_selection"] == "declared_producer_sku"
    assert qwen["needed"] == [] and qwen["needed_by_id"] == {}
    assert len(qwen["frames"]) == 139 and len(qwen["chunk_steps"]) == 139
    assert archive.frame_indexes(qwen) == list(range(139))
    assert qwen["chunk_steps"][0] == (1, 4212, 1)
    assert qwen["chunk_steps"][1] == (1, 4213, 1)
    assert qwen["chunk_steps"][-1] == (1, 4350, 1)
    assert len({step[1] for step in qwen["chunk_steps"]}) == 139
    assert {step[0] for step in qwen["chunk_steps"]} == {1}
    plan = engine.estimate_working_set(qwen["chunk_steps"])
    assert plan["unique_states"] == 139 and plan["queries"] == [1]
    assert plan["context_min"] == 4212 and plan["context_max"] == 4350
    assert qwen["context_tokens_min"] == 4212 and qwen["context_tokens_max"] == 4350
    assert qwen["observed_cached_tokens"] == 0 and qwen["designed_prefix_tokens"] == 3968
    assert qwen["case"]["workload"]["prefix_tokens"] == 0
    assert qwen["deployment_dp"] == 1 and qwen["deployment_dp_per_window"] is False
    assert qwen["frames"][0]["forward_id"] == "auto:0" and qwen["frames"][0]["chunk_forward_id"] == 117
    assert qwen["frames"][-1]["forward_id"] == "auto:138" and qwen["frames"][-1]["chunk_forward_id"] == 255
    assert all(frame.get("device_id") == "0" and "dp" not in frame for frame in qwen["frames"])
    assert [item["catalog_sku"] for item in qwen["hardware_candidates"]] == ["Ascend950PR_9579", "Ascend950DT_9582"]
    assert qwen["hardware_candidates"][0]["supply"] is True and qwen["hardware_candidates"][0]["applied"] is True
    assert qwen["hardware_candidates"][1]["supply"] is False and qwen["hardware_candidates"][1]["applied"] is False
    assert qwen["hardware_candidates"][1]["role"] == "contrary_template"
    assert "producer_deployment_setting_sku_applied" in qwen["diagnostics"]
    assert "hardware_sku_declared_not_serial_verified" in qwen["diagnostics"]
    assert "exact_score_withheld_until_physical_substrate" not in qwen["diagnostics"]
    assert "receipt_query_sum_139_disagrees_with_declared_input_4096" not in qwen["diagnostics"]
    assert qwen_poison["diagnostics"] == qwen["diagnostics"]
    assert qwen_poison["frames"] == qwen["frames"]
    assert qwen_poison["needed"] == qwen["needed"]
    assert qwen_poison["chunk_steps"] == qwen["chunk_steps"]
    assert qwen_poison["structural_sha256"] == qwen["structural_sha256"]
    assert qwen_poison["sku"] == qwen["sku"]
    assert qwen["case"]["runtime"]["kernels"]["moe_token_partition"] == MC2_TP_CALLER
    assert "native_moe_protocol" not in qwen["case"]["runtime"]["kernels"]
    assert qwen_poison["case"]["runtime"]["kernels"] == qwen["case"]["runtime"]["kernels"]
    assert "moe_token_partition" not in (a2["case"]["runtime"].get("kernels") or {})
    assert "moe_token_partition" not in (kimi["case"]["runtime"].get("kernels") or {})

    assert kimi["single_sku_case"] is True and kimi["supply_kind"] == "single_sku" and kimi["sku"]
    assert [frame["forward_id"] for frame in kimi["frames"]] == ["prefill:0", "prefill:1", "prefill:2"]
    assert [step[1] for step in kimi["chunk_steps"]] == [0, 8064, 16128]

    same = engine.priced_rate_signature("Ascend950PR_9579")
    assert same and same == engine.priced_rate_signature("Ascend950PR_9579")
    assert same != engine.priced_rate_signature("Ascend950DT_9582")
    invariant = archive._supply_decision({"sku": ""}, {"hardware_candidates": [
        {"role": "catalog_peer", "catalog_sku": "Ascend910B2", "applied": False, "declared_identity": "B2"},
        {"role": "catalog_peer", "catalog_sku": "Ascend910B2", "applied": False, "declared_identity": "B2-again"},
    ]})
    assert invariant["kind"] == "conditional_invariant"
    assert invariant["sku"] == "Ascend910B2" and invariant["not_from_measured_times"] is True
    assert engine.target_step_ms("captured_forward", "abc", [1.5]) == 1.5
    assert engine.target_step_ms("captured_forward", "abc", [1.5, 1.6]) is None
    assert engine.target_step_ms("captured_forward", "", [1.5]) is None
    assert engine.target_step_ms("other", "abc", [1.5]) is None


def test_forged_candidate_and_a2_stay_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """A contrary row and an A2 template alias are not priced."""
    def _forbidden(*_args, **_kwargs):
        raise AssertionError("body_forward on an unknown supply")

    monkeypatch.setattr(body, "body_forward", _forbidden)
    modeling.clear_caches()
    rows = _rows()
    qwen_resolved = _resolve(rows[QWEN])
    two = json.loads(json.dumps(qwen_resolved))
    two["geometry"]["hardware_candidates"][1]["applied"] = True
    two["geometry"]["hardware_candidates"][1]["role"] = "producer_deployment_setting"
    two_probe = modeling._archive_probe(two)
    assert two_probe["supply_kind"] == "unknown" and two_probe["sku"] == ""
    swapped = json.loads(json.dumps(qwen_resolved))
    swapped["geometry"]["hardware_candidates"][0]["applied"] = False
    swapped["geometry"]["hardware_candidates"][1]["applied"] = True
    swapped["geometry"]["hardware_candidates"][1]["role"] = "producer_deployment_setting"
    swapped_probe = modeling._archive_probe(swapped)
    assert swapped_probe["supply_kind"] == "unknown"
    assert swapped_probe["sku"] != "Ascend950DT_9582"

    a2 = modeling._archive_probe(_resolve(rows[A2]))
    forged_case = json.loads(json.dumps(_resolve(rows[A2])))
    forged_case["case"]["machine"]["sku"] = "Ascend910B4"
    forged_case["geometry"]["hardware_candidates"][1]["applied"] = True
    forged_probe = modeling._archive_probe(forged_case)
    assert forged_probe["supply_kind"] == "unknown" and forged_probe["sku"] == ""
    assert forged_probe["case"]["machine"].get("sku") in {None, "", "Ascend910B4"}
    published = archive.publish_archive_prediction(a2, {"capture_id": A2, "phase": "prefill", "hardware_tier": "A2"})
    refused = archive.price_archive_scenario(a2, "Ascend910B4", {"phase": "prefill"})
    assert published["status"] == "insufficient_evidence" and published["ok"] is False
    assert published["predicted_step_ms"] is None
    assert "prediction_boundary" not in published and "boundary_samples" not in published
    assert published["sku"] == "" and published["hardware_selection"] == "not_selected"
    assert refused["priced"] is False and refused["reason"] == "not_the_agreed_hardware_supply"
    assert all(item.get("catalog_sku") != "Ascend910B4" or item.get("priced") is False for item in published["hardware_candidates"])
    scored = gate.score_fleet_row(
        {"capture_id": A2, "suite": "wave5_20261031", "phase": "prefill", "hardware_tier": "A2"},
        _window(["phase=prefill|device_id=4|forward_id=prefill:0"], "prefill", capture_id=A2, hardware_tier="A2"),
        published,
    )
    assert scored["comparison"] != "compared"
    assert scored["key_denominator"] == 1 and scored["key_missing"] == 1 and scored["key_matched"] == 0


def test_four_qwen_frames_are_distinct_declared_prices(monkeypatch: pytest.MonkeyPatch) -> None:
    """Four real contexts stay unique. The parsed case is compiled once for this window."""
    calls = {"n": 0}
    original = body.body_forward

    def _count(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(body, "body_forward", _count)
    modeling.clear_caches()
    qwen = modeling._archive_probe(_resolve(_rows()[QWEN]))
    calls["n"] = 0
    published = archive.publish_archive_prediction(
        qwen, {"capture_id": QWEN, "phase": "decode", "hardware_tier": "A5"}, material_indexes=MATERIAL,
    )
    assert calls["n"] == 4
    assert modeling._STEP_EQUIVALENCE == {}
    assert published["status"] == "modeled" and published.get("ok") is not False
    assert published["material_window"] is True and published["ordinary_frame_count"] == 139
    assert published["predicted_step_ms"] is None
    assert published["exact"] is False and published["sku"] == "Ascend950PR_9579"
    assert published["hardware_selection"] == "declared_producer_sku"
    assert published["target_timing_used_to_fit"] is False
    assert published["attribution"]["body"] == "recomputed_body_from_genuine_declaration"
    assert published["attribution"]["wave5_original_in_sample_row"] == "separate"
    assert published["hardware_supply"]["serial_certified"] is False
    assert published["hardware_supply"]["role"] == "producer_deployment_setting"
    assert published["hardware_supply"]["exact"] is False
    stats = published["engine_stats"]
    assert stats["compilations"] == 1 and stats["engine_calls"] == 4 and stats["reused_states"] == 0
    assert stats["working_set"] == 4 and stats["invariant_geometry"] == "verified"
    assert stats["invariant_ops_reused"] > 0 and stats["active_ops"] > 0
    samples = published["boundary_samples"]
    assert len(samples) == 4
    contexts = [item["context_tokens"] for item in samples]
    assert contexts == [4212, 4213, 4214, 4350]
    values = [item["boundary_ms"] for item in samples]
    assert len(set(values)) == 4
    assert all(isinstance(value, float) and value > 0 and value != TEMPLATE_PRICE for value in values)
    assert all(item["tokens_per_sequence"] == 1 for item in samples)
    assert all(item["hardware_supply"]["sku"] == "Ascend950PR_9579" for item in samples)
    assert all(item["hardware_supply"]["exact"] is False and item["hardware_supply"]["serial_certified"] is False for item in samples)
    assert published["hardware_candidates"][0]["priced"] is True
    assert published["hardware_candidates"][1]["priced"] is False
    assert published["hardware_candidates"][1]["catalog_sku"] == "Ascend950DT_9582"
    keys = [item["key"] for item in samples]
    scored = gate.score_fleet_row(
        {"capture_id": QWEN, "suite": "wave5_20261031", "phase": "decode", "hardware_tier": "A5"},
        _window(keys, "decode", capture_id=QWEN, hardware_tier="A5", source_sha=published["source_sha256"]),
        published,
    )
    assert scored["comparison"] == "compared"
    assert scored["key_denominator"] == 4 and scored["key_matched"] == 4 and scored["key_missing"] == 0
    args = archive.parse_args(["--jsonl", str(JSONL), "--out", "/tmp/unused-c4-out.json"])
    assert args.material_indexes == "" and args.ordinary_four_body is False
    with pytest.raises(SystemExit):
        archive.main(["--jsonl", str(JSONL), "--out", "/tmp/unused-c4-out.json", "--ordinary-four-body", "--material-indexes", "0,1"])


def test_defaulted_prefill_sequences_keep_a_conditional_forecast() -> None:
    """Unknown request count does not drop the forecast or certify the row."""
    priced = {
        "ok": True,
        "status": "modeled",
        "predicted_step_ms": 1.25,
        "predicted_operator_ms": 1.0,
        "engine": "mindie_sim.prediction.body.body_forward",
    }
    probe = {
        "ok": True,
        "phase": "prefill",
        "diagnostics": ["sequences_per_replica_absent_on_frame_uses_one_request"],
        "supply": {"sku": "Ascend950PR_9579", "kind": "declared_producer_sku"},
        "frames": [{"query_rows": 8, "context_tokens": 0, "sequences_per_replica": 1}],
        "chunk_steps": [(8, 0, 1)],
        "hardware_candidates": [],
        "hardware_selection": "declared_producer_sku",
    }
    record = archive._publication(probe, {"phase": "prefill"}, priced, False, [0])
    assert record["status"] == "conditional"
    assert record["predicted_step_ms"] == 1.25
    assert record["coverage"]["modeled"] is False
    assert record["coverage"]["sequence_count_certified"] is False
    assert "ok" not in record
    assert "sequence_count_not_certified:conditional_forecast_retained" in record["diagnostics"]
    proven = archive._publication({**probe, "diagnostics": []}, {"phase": "prefill"}, priced, False, [0])
    assert proven["status"] == "modeled"
    assert proven["coverage"]["modeled"] is True
    decoded = archive._publication({**probe, "phase": "decode"}, {"phase": "decode"}, priced, False, [0])
    assert decoded["status"] == "modeled"
    assert decoded["predicted_step_ms"] == 1.25


def test_one_qwen_source_frame_keeps_the_raw_target() -> None:
    """Index 0 stays a real keyed span. Expert GEMM uses 768, not a dense 6144 axis."""
    modeling.clear_caches()
    row = _rows()[QWEN]
    probe = modeling._archive_probe(_resolve(row))
    published = archive.publish_archive_prediction(
        probe, {"capture_id": QWEN, "phase": "decode", "hardware_tier": "A5"}, material_indexes=(0,),
    )
    sample = published["boundary_samples"][0]
    observation = observations.extract_capture_observations(gate.prediction_config(row))
    population = scoring.observed_boundary_population(observation, "per_forward_window")
    observed = dict(zip(population["keys"], population["values"]))[sample["key"]]
    reason, relative = scoring._pair_error(sample["boundary_ms"], observed)
    model = probe["case"]["model"]
    built = target_graphs(parse_case(probe["case"]), phase="decode", tokens=1, context=4212, sequences=1, scope="body")
    ops = list(next(iter(built.values())))
    down = next(op for op in ops if op.op_id == "s0.l0.expert_down")
    up = next(op for op in ops if op.op_id == "s0.l0.expert_up")
    held = _window([sample["key"]], "decode", capture_id=QWEN, hardware_tier="A5", source_sha=published["source_sha256"])
    held["measurements"]["per_forward_window"]["samples"][0]["observed_ms"] = observed
    scored = gate.score_fleet_row(row, held, published)
    assert sample["key"] == "phase=decode|device_id=0|forward_id=auto:0"
    assert sample["context_tokens"] == 4212 and sample["tokens_per_sequence"] == 1
    assert published["sku"] == "Ascend950PR_9579"
    assert held["measurements"]["per_forward_window"]["samples"][0]["observed_ms"] == observed
    assert reason == "" and relative == pytest.approx(abs(sample["boundary_ms"] - observed) / abs(observed))
    assert scored["comparison"] == "compared" and scored["key_denominator"] == 1 and scored["key_matched"] == 1
    assert scored["group_passed_10pct"] is (relative <= 0.10)
    assert scored["keys_over_10pct"] == (0 if relative <= 0.10 else 1)
    assert model["moe_intermediate_size"] == 768 and model["intermediate_size"] == 768 and model["ffn"] == "moe"
    assert list(up.local_shape) == [2, 1536, 2048] and list(down.local_shape) == [2, 2048, 768]
    assert all(6144 not in op.local_shape for op in ops if op.family == "grouped_gemm")
    kernels = probe["case"]["runtime"]["kernels"]
    assert kernels["moe_token_partition"] == MC2_TP_CALLER
    assert "native_moe_protocol" not in kernels
    assert any(op.family == "allgather" for op in ops)
    assert any(
        dict(op.metadata).get("native_kind") == "ConcatD" for op in ops if op.metadata
    )


def test_caller_declaration_ignores_target_and_rejects_other_routes() -> None:
    """Timing edits do not change the caller. Quantized and unequal EP stay generic."""
    modeling.clear_caches()
    clean = _resolve(_rows()[QWEN])
    poisoned = json.loads(json.dumps(clean))
    poisoned["observed_ms"] = 6.909
    poisoned["predicted_ms"] = 7.249
    poisoned["measurements"] = {"per_forward_window": {"samples": [{"observed_ms": 1.0}]}}
    poisoned.pop("body_forward_span_ms", None)
    original = modeling._archive_probe(clean)
    retargeted = modeling._archive_probe(poisoned)
    assert original["case"]["runtime"]["kernels"]["moe_token_partition"] == MC2_TP_CALLER
    assert retargeted["case"]["runtime"]["kernels"] == original["case"]["runtime"]["kernels"]
    assert "native_moe_protocol" not in original["case"]["runtime"]["kernels"]

    unequal = json.loads(json.dumps(clean))
    unequal["case"]["runtime"]["ep"] = unequal["case"]["runtime"]["tp"] + 4
    unequal_probe = modeling._archive_probe(unequal)
    assert "moe_token_partition" not in (unequal_probe["case"]["runtime"].get("kernels") or {})

    quantized = json.loads(json.dumps(clean))
    quantized["case"]["model"]["quantization"] = "w8a8"
    quantized["case"]["model"]["weight_dtype"] = "int8"
    quantized_probe = modeling._archive_probe(quantized)
    assert "moe_token_partition" not in (quantized_probe["case"]["runtime"].get("kernels") or {})
