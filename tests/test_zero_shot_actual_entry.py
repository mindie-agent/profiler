"""Focused tests for original measured-entry recovery and row-local geometry.

[Role]
  Exercise producer-JSON projection, row-local sequence/query-token geometry,
  pipeline-parallel transfer accounting, and measurement-blindness contracts
  consumed by the zero-shot prediction path.

[Invariants]
  * tpot_mean_s / ttft_mean_s are seconds and are exposed as milliseconds.
  * Graph-bucket padding never increases the number of valid local sequences.
  * Per-cell entry rows are target-local statuses, not copies of an aggregate.
  * Case-level measured metadata or service_regimes never move predictions.

[Timeouts & Locks]
  Bounded local tmp_path JSON/CSV fixtures; no network, subprocess or sleep.

[Side-Effect Policy]
  All generated artifacts live under pytest ``tmp_path``; repository files are
  read-only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
MODEL_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
QWEN36_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen36_highconc_c4.json"
GLM_FLASH_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm53flash_tp8_c4_p8k.json"

sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_actual_entry as actual  # noqa: E402
import zero_shot_piecewise_validation as z  # noqa: E402


@pytest.fixture(scope="module")
def compact_cases(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    base_dir = tmp_path_factory.mktemp("actual_entry_cases")
    out: dict[str, Path] = {}
    for key, src in (("qwen38", MODEL_CASE), ("qwen36", QWEN36_CASE)):
        doc = json.loads(src.read_text(encoding="utf-8"))
        doc["model"]["layers"] = 4
        if "layer_plans" in doc["model"]:
            doc["model"]["layer_plans"] = list(doc["model"]["layer_plans"])[:4]
        dst = base_dir / f"compact_{key}.json"
        dst.write_text(json.dumps(doc), encoding="utf-8")
        out[key] = dst
    return out


def _write_measured(root: Path, tag: str, *, tpot_s=0.815898, ttft_s=16.771002,
                    completion=(4,)) -> Path:
    path = root / "out" / "case" / "measured" / f"{tag}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "tag": tag, "mode": "profile_decode", "prompt_tokens": 131072,
        "max_tokens": 64, "concurrency": 1, "success": 1,
        "ttft_mean_s": ttft_s, "tpot_mean_s": tpot_s,
        "streams": [{"ok": True, "ttft_s": ttft_s, "e2e_s": ttft_s + 3 * tpot_s,
                     "completion_tokens": n, "chunks": n} for n in completion],
    }), encoding="utf-8")
    return path


def _cell(tag: str, *, steps=63, tpot=None, ttft=None, concurrency=1, dp=16,
          graph_bucket=0):
    spec = z.CellSpec(tag, "out", "decode", MODEL_CASE, "Qwen3.8-27B", 131072,
                      concurrency, 64, 1, dp, dp, 1, (), graph_bucket)
    trace = z.KernelTrace(float(steps) * 1000.0, {}, {"MatMulV3": float(steps) * 1000.0},
                          {"MatMulV3": steps}, tuple(1000.0 for _ in range(steps)))
    return z.MeasuredCell(spec, (), trace, ttft, tpot, 1.0, steps, True)


def test_source_recovery_uses_seconds_to_milliseconds_and_keeps_device_steps(tmp_path):
    _write_measured(tmp_path, "foo")
    cell = _cell("foo")
    recovered = actual.apply_original_observations([cell], roots=(tmp_path,))[0]
    assert recovered.tpot_ms == pytest.approx(815.898)
    assert recovered.ttft_ms == pytest.approx(16771.002)
    assert recovered.request_tokens == 4
    assert recovered.trace_quality == "ok"
    assert recovered.step_trace_ms == pytest.approx(1.0) and recovered.decode_steps == 63

    good = _cell("good", steps=63)
    _write_measured(tmp_path, "good", completion=(64,))
    recovered_good = actual.apply_original_observations([good], roots=(tmp_path,))[0]
    assert recovered_good.trace_quality == "ok"
    assert recovered_good.request_tokens == 64


def test_original_record_wins_and_conflict_is_explicit(tmp_path):
    _write_measured(tmp_path, "keep", tpot_s=2.0, ttft_s=3.0)
    cell = _cell("keep", tpot=1.0, ttft=2.0)
    recovered = actual.apply_original_observations([cell], roots=(tmp_path,))[0]
    assert recovered.tpot_ms == pytest.approx(2000.0)
    assert recovered.ttft_ms == pytest.approx(3000.0)
    assert recovered.source_conflict == "tpot,ttft"


def test_ttft_is_preserved_without_tpot_and_exact_tag_is_required(tmp_path):
    path = tmp_path / "out" / "case" / "measured" / "ttft_only.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"tag": "ttft_only", "ttft_mean_s": 1.25,
                                "streams": [{"ttft_s": 1.25, "completion_tokens": 2,
                                             "itl_mean_s": 9.0, "itl_p50_s": 8.0}]}))
    observations = actual.load_observations(["ttft_only"], roots=(tmp_path,))
    assert observations["ttft_only"].ttft_ms == pytest.approx(1250.0)
    assert observations["ttft_only"].tpot_ms is None
    wrong = tmp_path / "out" / "case" / "measured" / "wrong.json"
    wrong.write_text(json.dumps({"tag": "other", "tpot_mean_s": 1.0, "ttft_mean_s": 1.0}))
    assert actual.load_observations(["wrong"], roots=(tmp_path,)) == {}


def test_public_benchmark_loader_recovers_original_client_fields(tmp_path):
    _write_measured(tmp_path, "public")
    cell = _cell("public")
    jsonl = tmp_path / "cells.jsonl"
    jsonl.write_text(json.dumps(z.cell_to_dict(cell)) + "\n", encoding="utf-8")
    loaded = z.load_benchmark_jsonl(jsonl, roots=(tmp_path,))
    assert len(loaded) == 1
    assert loaded[0].tpot_ms == pytest.approx(815.898)
    assert loaded[0].ttft_ms == pytest.approx(16771.002)
    assert loaded[0].request_tokens == 4


def test_row_local_sequences_and_query_tokens_are_not_bucket_inflated():
    base = z.CellSpec("row", "out", "decode", MODEL_CASE, "Qwen3.8-27B", 131072,
                      8, 64, 1, 8, 8, 1, (1, 2, 4, 8, 16, 32, 64, 128), 128)
    local = z.replace(base, sequences_per_replica=3, tokens_per_sequence=6)
    geometry = z._geometry(local, "decode")
    assert geometry.batch == 3
    assert geometry.local_batch == 3
    assert {request.q_len for request in geometry.requests} == {6}
    assert z._local_batch(local) == 3
    padded = z._geometry(z.replace(base, graph_buckets=(1, 128), graph_bucket=128), "decode")
    assert padded.batch == 1


def test_cell_entry_reports_target_local_pass_uncovered_and_above():
    cell = _cell("entry", steps=2, tpot=10.0)
    comparison = z.Comparison("L4", "decode_step_tpot", "service", 9.0, 10.0,
                              "service_framework", "g", "host", "f", -1)
    rows = actual.cell_entry(cell, (comparison,),
                             (("L4", "decode_step_tpot"), ("L4", "prefill_step_ttft"),
                              ("L3", "decode_step_trace")))
    by_target = {row["target"]: row for row in rows["targets"]}
    assert by_target["decode_step_tpot"]["status"] == "pass"
    assert by_target["prefill_step_ttft"]["status"] == "uncovered"
    bad = z.Comparison("L4", "decode_step_tpot", "service", 12.0, 10.0,
                       "service_framework", "g", "host", "f", -1)
    rows = actual.cell_entry(cell, (bad,), (("L4", "decode_step_tpot"),))
    assert rows["targets"][0]["status"] == "above_10pct"
    assert rows["targets"][0]["errors"] == pytest.approx([0.2])


def test_duplicate_measured_tags_fail_closed(tmp_path):
    first = tmp_path / "root_a" / "out" / "case" / "measured" / "dup.json"
    second = tmp_path / "root_b" / "out" / "case" / "measured" / "dup.json"
    for path in (first, second):
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"tag": "dup", "tpot_mean_s": 1.0, "ttft_mean_s": 2.0}))
    with pytest.raises(ValueError, match="duplicate_measured_tag"):
        actual.load_observations(["dup"], roots=(tmp_path / "root_a", tmp_path / "root_b"))


def test_cell_roundtrip_preserves_row_local_and_source_fields():
    cell = _cell("roundtrip")
    cell = z.replace(cell, request_tokens=4, source_conflict="tpot",
                     source_measured="/raw/measured/roundtrip.json",
                     spec=z.replace(cell.spec, sequences_per_replica=3, tokens_per_sequence=6))
    restored = z.cell_from_dict(z.cell_to_dict(cell))
    assert restored.request_tokens == 4 and restored.source_conflict == "tpot"
    assert restored.source_measured == "/raw/measured/roundtrip.json"
    assert restored.spec.sequences_per_replica == 3 and restored.spec.tokens_per_sequence == 6


def test_prefill_chunks_use_declared_budget_and_growing_context(monkeypatch):
    monkeypatch.setattr(z, "_max_batched_tokens", lambda spec: 1024)
    spec = z.CellSpec("pf", "out", "prefill", MODEL_CASE, "Qwen3.8-27B",
                      4096, 2, 1, 4, 1, 1, 1)
    chunks = z._prefill_chunk_geometries(spec)
    assert len(chunks) == 4
    assert [chunk.requests[0].q_len for chunk in chunks] == [1024] * 4
    assert [chunk.requests[0].kv_len for chunk in chunks] == [1024, 2048, 3072, 4096]
    assert all(chunk.batch == 2 for chunk in chunks)


def test_case_level_measured_metadata_cannot_move_prediction(tmp_path, compact_cases):
    qwen38 = compact_cases["qwen38"]
    source = json.loads(qwen38.read_text(encoding="utf-8"))

    def poison(value):
        if isinstance(value, dict):
            return {key: (1e9 if isinstance(item, (int, float)) and not isinstance(item, bool)
                          else poison(item)) for key, item in value.items()}
        if isinstance(value, list):
            return [poison(item) for item in value]
        return value

    source.setdefault("runtime", {}).setdefault("kernels", {})["service_regimes"] = [
        {"match": {"hardware": "poison"}, "mean_ms": 1e9}]
    source["runtime"]["metadata"] = {"tpot_mean_s": 1e9, "ttft_mean_s": 1e9}
    source["runtime"]["kernels"] = {
        key: (value if key == "lowerings" else poison(value))
        for key, value in source["runtime"]["kernels"].items()
    }
    poisoned = tmp_path / "poisoned_case.json"
    poisoned.write_text(json.dumps(source), encoding="utf-8")
    spec = z.CellSpec("blind", "out", "decode", qwen38, "Qwen3.8-27B",
                      1024, 2, 8, 4, 1, 1, 1, synthetic_layers=2)
    clean = z.predict_cell(spec)
    dirty = z.predict_cell(z.replace(spec, model_case=poisoned))
    assert dirty.body_ms == pytest.approx(clean.body_ms)
    assert dirty.per_layer == clean.per_layer
    assert [(row.mechanism, row.duration_ms) for row in dirty.rows] == \
        [(row.mechanism, row.duration_ms) for row in clean.rows]


def test_glm_runtime_service_regimes_poison_cannot_move_prediction(tmp_path):
    source = json.loads(GLM_FLASH_CASE.read_text(encoding="utf-8"))
    source["runtime"].setdefault("kernels", {})["service_regimes"] = [
        {"match": {"hardware": "poison"}, "fixed_us": 26.922976811594204,
         "mean_ms": 1e9}]
    source["runtime"].setdefault("metadata", {})["tpot_mean_s"] = 1e9
    poisoned = tmp_path / "glm_poison.json"
    poisoned.write_text(json.dumps(source), encoding="utf-8")
    spec = z.CellSpec("glm_blind", "out", "decode", GLM_FLASH_CASE,
                      "GLM-5.3/W8A8-MXFP8", 1024, 2, 8, 8, 1, 1, 1,
                      notes=("catalog:glm-5.3", "override_model"))
    clean = z.predict_cell(spec)
    dirty = z.predict_cell(z.replace(spec, model_case=poisoned))
    assert clean.layers == 78
    assert dirty.body_ms == pytest.approx(clean.body_ms)
    assert dirty.per_layer == clean.per_layer


def test_pipeline_parallel_stage_transfer_is_not_identical_to_pp1(compact_cases):
    spec = z.CellSpec("pp", "out", "decode", compact_cases["qwen36"], "Qwen3.6-27B",
                      128, 1, 2, 1, 1, 1, 1)
    pp1 = z.predict_cell(spec)
    pp2 = z.predict_cell(z.replace(spec, pp=2))
    assert pp2.body_ms > pp1.body_ms
    assert any(row.kind == "PP" and row.mechanism == "collective" for row in pp2.rows)
    assert "pp_transfers:1" in pp2.notes


def test_cohort_launch_config_is_the_normal_geometry_source(tmp_path, monkeypatch):
    cohort = tmp_path / "qwen38_27b_dp4tp2.json"
    cohort.write_text(json.dumps({
        "dp": 4, "tp": 2, "max_num_batched_tokens": 8192,
        "compilation_config": {"cudagraph_capture_sizes": [1, 2, 4, 8]},
        "additional_config": {"enable_mlapo": True, "enable_fused_mc2": 1}}))
    monkeypatch.setattr(z, "_cohort_case", lambda spec: cohort)
    spec = z.CellSpec("qwen38_27b_dp4tp2_decode_1024_c16", "out", "decode",
                      MODEL_CASE, "Qwen3.8-27B", 1024, 16, 64, 2, 4, 1, 1)
    runtime = z._raw_case(spec)["runtime"]
    assert (runtime["tp"], runtime["dp"], runtime["ep"], runtime["pp"]) == (2, 4, 1, 1)
    assert runtime["max_num_batched_tokens"] == 8192
    assert runtime["graph_buckets"] == [1, 2, 4, 8]
    assert runtime["metadata"]["additional_config"]["enable_fused_mc2"] == 1


def test_actual_cohort_machine_expands_to_declared_device_domain(tmp_path, monkeypatch):
    cohort = tmp_path / "dsv41_dp16tp1ep16.json"
    cohort.write_text(json.dumps({"dp": 16, "tp": 1, "max_num_batched_tokens": 8192}))
    monkeypatch.setattr(z, "_cohort_case", lambda spec: cohort)
    spec = z.CellSpec("dsv41_dp16tp1ep16_dc_1k_c1", "out", "decode",
                      MODEL_CASE, "Qwen3.8-27B", 1024, 1, 64, 1, 16, 16, 1)
    machine = z._raw_case(spec)["machine"]
    assert machine["num_devices"] >= 16
    assert machine["device"]["rates"]["link_hccs"] > 0


def test_public_prediction_is_invariant_to_opaque_labels_and_suffixes(compact_cases):
    spec = z.CellSpec("qwen38_27b_dp4tp2_decode_1024_c1", "out", "decode",
                      compact_cases["qwen38"], "Qwen3.8-27B", 1024, 1, 128, 2, 4, 1, 1,
                      (1, 2, 4, 8), 1, ("graph_bucket_declared",))
    original = z.predict_cell(spec)
    renamed = z.predict_cell(z.replace(
        spec, cell_id="opaque_l2_e8_k2_pd_64k_p8k_c8", model_label="opaque-label"))
    assert renamed.layers == original.layers
    assert renamed.body_ms == pytest.approx(original.body_ms)
    assert renamed.per_layer == original.per_layer
    assert [(row.name, row.count, row.duration_ms) for row in renamed.rows] == \
        [(row.name, row.count, row.duration_ms) for row in original.rows]
    renamed_spec = z.replace(spec, cell_id="opaque_l2_e8_k2_pd_64k_p8k_c8", model_label="opaque-label")
    assert z._structure_fingerprint(renamed_spec) == z._structure_fingerprint(spec)

    structural = z.predict_cell(z.replace(
        spec, synthetic_layers=2, synthetic_experts=8, synthetic_topk=2))
    assert structural.layers == 2
    assert structural.body_ms != pytest.approx(original.body_ms)


def test_pp_prefill_uses_actual_hidden_rows_and_stage_link(compact_cases):
    base = z.CellSpec("pp_pf", "out", "prefill", compact_cases["qwen38"], "Qwen3.8-27B",
                      1024, 1, 1, 2, 4, 1, 1, synthetic_layers=2)
    small = z.predict_cell(z.replace(base, pp=2, prompt_tokens=1024))
    large = z.predict_cell(z.replace(base, pp=2, prompt_tokens=2048))
    pp1 = z.predict_cell(base)
    rows_small = [row for row in small.rows if row.kind == "PP"]
    rows_large = [row for row in large.rows if row.kind == "PP"]
    assert pp1.body_ms == pytest.approx(
        z.predict_cell(z.replace(base, pp=1, prompt_tokens=1024)).body_ms)
    assert not [row for row in pp1.rows if row.kind == "PP"]
    assert rows_small and rows_large
    assert rows_small[0].name.startswith("pp_transfer:s0->") and "link_" in rows_small[0].formula
    assert "startup_ms=" in rows_small[0].formula
    assert rows_large[0].duration_ms > rows_small[0].duration_ms * 1.5
    assert small.body_ms > pp1.body_ms and large.body_ms > small.body_ms


def test_pp_inter_node_placement_selects_roce_formula(compact_cases):
    spec = z.CellSpec("pp_inter", "out", "prefill", compact_cases["qwen38"], "Qwen3.8-27B",
                      1024, 1, 1, 8, 1, 1, 2, synthetic_layers=2)
    pred = z.predict_cell(spec)
    rows = [row for row in pred.rows if row.kind == "PP"]
    assert rows and "link_roce" in rows[0].formula


def test_pp2_decode_transfer_is_in_phase_body_and_service_once(compact_cases):
    base = z.CellSpec("pp_dc", "out", "decode", compact_cases["qwen38"], "Qwen3.8-27B",
                      1024, 1, 128, 2, 4, 1, 1, synthetic_layers=2)
    pp1 = z.predict_cell(base)
    pp2 = z.predict_cell(z.replace(base, pp=2))
    transfer = sum(row.duration_ms for row in pp2.rows if row.kind == "PP")
    assert transfer > 0.0
    assert pp2.body_ms == pytest.approx(pp1.body_ms + transfer)
    assert pp2.decode_body_ms == pytest.approx(pp2.body_ms)
    assert z._phase_body(pp2, "decode") == pytest.approx(pp2.body_ms)
    assert z._phase_body(pp1, "decode") == pytest.approx(pp1.body_ms)


def test_missing_or_wrong_deploy_identity_is_rejected_without_template(tmp_path):
    base = z.CellSpec("glm51_dp16tp1ep16_dc_1k_c1", "out", "decode", GLM_FLASH_CASE,
                      "GLM-5.1/W4A4C8", 1024, 1, 64, 1, 16, 16, 1,
                      require_source=True)
    missing = z.predict_cell(base)
    assert missing.layers == 0 and "deploy_identity_missing_or_mismatch" in missing.notes

    cfg_a = tmp_path / "GLM-5.3-W8A8C8-mxfp8" / "config.json"
    cfg_b = tmp_path / "GLM-5.1-w4a4c8-mxfp4" / "config.json"
    cfg_a.parent.mkdir(parents=True)
    cfg_b.parent.mkdir(parents=True)
    cfg_a.write_text(json.dumps({"model_type": "glm53", "head_dim": 192}), encoding="utf-8")
    cfg_b.write_text(json.dumps({"model_type": "glm51", "head_dim": 64}), encoding="utf-8")
    sha_a = hashlib.sha256(cfg_a.read_bytes()).hexdigest()
    sha_b = hashlib.sha256(cfg_b.read_bytes()).hexdigest()
    wrong = z.predict_cell(z.replace(
        base, source_config=cfg_a, source_config_sha256=sha_a, source_deploy_sha256=sha_b))
    assert wrong.layers == 0 and "deploy_identity_missing_or_mismatch" in wrong.notes


def test_pp2_decode_service_includes_prefill_transfer_not_only_body(monkeypatch, compact_cases):
    base = z.CellSpec("pp_dc_service", "out", "decode", compact_cases["qwen38"], "Qwen3.8-27B",
                      4096, 1, 64, 2, 4, 1, 1, synthetic_layers=2)
    monkeypatch.setattr(z, "_max_batched_tokens", lambda spec: 1024)
    pp1 = z.predict_cell(base)
    pp2 = z.predict_cell(z.replace(base, pp=2))
    decode_transfer = sum(
        row.duration_ms for row in pp2.rows
        if row.kind == "PP" and row.name.endswith(":c1") and row.name.startswith("pp_transfer:s0->8:c1")
    )
    assert pp2.body_ms == pytest.approx(pp1.body_ms + decode_transfer)
    assert pp2.ttft_ms > pp1.ttft_ms + decode_transfer


def test_pp_prefill_multi_chunk_transfer_startups(monkeypatch, compact_cases):
    spec = z.CellSpec("pp_pf_chunks", "out", "prefill", compact_cases["qwen38"], "Qwen3.8-27B",
                      4096, 1, 1, 2, 4, 1, 2)
    monkeypatch.setattr(z, "_max_batched_tokens", lambda item: 1024)
    pp2 = z.predict_cell(spec)
    rows = [row for row in pp2.rows if row.kind == "PP"]
    assert len(rows) == 4
    assert [row.name for row in rows] == [
        "pp_transfer:s0->8:c1", "pp_transfer:s0->8:c2",
        "pp_transfer:s0->8:c3", "pp_transfer:s0->8:c4"]
    assert all("startup_ms=0.005" in row.formula for row in rows)
    assert sum(row.duration_ms for row in rows) > 1.5 * rows[0].duration_ms


def test_distinct_declared_max_tokens_controls_chunk_count(tmp_path, compact_cases):
    case_dir = tmp_path / "out" / "qwen_probe"
    case_dir.mkdir(parents=True)
    cases = tmp_path / "cases"
    cases.mkdir(parents=True)
    (cases / "qwen_probe.json").write_text(json.dumps({
        "tp": 2, "dp": 4, "max_num_batched_tokens": 4096}))
    spec = z.CellSpec("qwen_probe_pf_32768_c1", "out", "prefill", compact_cases["qwen38"],
                      "Qwen3.8-27B", 32768, 1, 1, 2, 4, 1, 1,
                      synthetic_layers=2, source_case_dir=case_dir)
    chunks = z._prefill_chunk_geometries(spec)
    assert z._max_batched_tokens(spec) == 4096
    assert [g.requests[0].q_len for g in chunks] == [4096] * 8
    pp1 = z.predict_cell(z.replace(spec, pp=1))
    pp2 = z.predict_cell(z.replace(spec, pp=2))
    rows = [row for row in pp2.rows if row.kind == "PP"]
    assert len(rows) == 8
    assert pp2.body_ms > pp1.body_ms


def test_lane_scope_miss_does_not_reject_the_model_and_does_not_borrow_dispatch(tmp_path, monkeypatch):
    sizes = [1, 2, 4, 8, 16, 32]
    status = {
        "spec": {
            "tp": 2, "dp": 4,
            "additional_config": {"enable_flashcomm1": True},
            "compilation_config": {
                "cudagraph_mode": "FULL_DECODE_ONLY",
                "cudagraph_capture_sizes": sizes,
            },
        },
        "compilation_used": json.dumps({
            "cudagraph_mode": "FULL_DECODE_ONLY",
            "cudagraph_capture_sizes": sizes,
        }),
        "cells": [{"tag": "listed_decode", "rc": 0}],
    }
    case_dir = tmp_path / "historical_case"
    case_dir.mkdir()
    (case_dir / "status.json").write_text(json.dumps(status), encoding="utf-8")
    historical = z.CellSpec(
        "historical_decode", "bench", "decode", MODEL_CASE, "Qwen3.8-27B",
        128, 1, 8, 2, 4, 1, 1, source_case_dir=case_dir)
    withheld = z._lane_kwargs(historical)
    assert withheld.get("graph_dispatch") != "full_decode_only"
    assert z._geometry(historical, "decode").physical_gdn_rows() == (1, 1, 0)
    monkeypatch.setattr(
        "mindie_sim.prediction.structure.parse_case",
        lambda _raw: (_ for _ in ()).throw(RuntimeError("reached_model")))
    reached = z.predict_cell(historical)
    assert any("reached_model" in note for note in reached.notes)
    assert not any("source_cell_not_in_deployment" in note for note in reached.notes)
    tampered = z.predict_cell(z.replace(
        historical, source_reject_reason="source_override_contradicts_deployment"))
    assert tampered.layers == 0
    assert tampered.notes == ("source_override_rejected:source_override_contradicts_deployment",)
    listed = z.replace(historical, cell_id="listed_decode")
    admitted = z._lane_kwargs(listed)
    assert admitted.get("graph_dispatch") == "full_decode_only"
