"""Focused tests for original measured-entry recovery and row-local geometry.

[Role]
  Exercise the unaltered producer-JSON projection used by the 731-cell actual
  entry and the CellSpec row-local sequence/query-token geometry consumed by
  the zero-shot prediction path.

[Invariants]
  * tpot_mean_s / ttft_mean_s are seconds and are exposed as milliseconds.
  * An existing portable observation is never overwritten by source recovery.
  * A device trace whose step count contradicts the measured request tokens is
    marked by explicit producer provenance when one is supplied.
  * Graph-bucket padding never increases the number of valid local sequences.
  * Per-cell entry rows are target-local statuses, not copies of an aggregate.

[Timeouts & Locks]
  Bounded local tmp_path JSON/CSV fixtures; no network, subprocess or sleep.

[Side-Effect Policy]
  All generated artifacts live under pytest ``tmp_path``; repository files are
  read-only.
"""
from __future__ import annotations

import json
from pathlib import Path
import os

import pytest

pytest.importorskip("mindie_sim")

ROOT = Path(__file__).resolve().parents[1]
MODEL_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
ZERO_SHOT_JSONL = Path(os.environ.get("MINDIE_ZERO_SHOT_JSONL", ""))
PROVENANCE_ROOT = Path(os.environ.get("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT", ""))
HEADER_ORACLE = Path(os.environ.get("MINDIE_WEIGHT_HEADER_ARCHIVE", ""))

import sys
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_actual_entry as actual  # noqa: E402
import zero_shot_piecewise_validation as z  # noqa: E402


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
    # Bucket padding may label the graph, but it cannot add valid sequences.
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


def test_case_level_measured_metadata_cannot_move_prediction(tmp_path):
    source = json.loads(MODEL_CASE.read_text(encoding="utf-8"))

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
    source["runtime"]["kernels"] = poison(source["runtime"]["kernels"])
    poisoned = tmp_path / "poisoned_case.json"
    poisoned.write_text(json.dumps(source), encoding="utf-8")
    spec = z.CellSpec("blind", "out", "decode", MODEL_CASE, "Qwen3.8-27B",
                      1024, 2, 8, 4, 1, 1, 1)
    clean = z.predict_cell(spec)
    dirty = z.predict_cell(z.replace(spec, model_case=poisoned))
    assert dirty.body_ms == pytest.approx(clean.body_ms)
    assert dirty.per_layer == clean.per_layer
    assert [(row.mechanism, row.duration_ms) for row in dirty.rows] == \
        [(row.mechanism, row.duration_ms) for row in clean.rows]


def test_glm_runtime_service_regimes_poison_cannot_move_prediction(tmp_path):
    source_path = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm53flash_tp8_c4_p8k.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source["runtime"].setdefault("kernels", {})["service_regimes"] = [
        {"match": {"hardware": "poison"}, "fixed_us": 26.922976811594204,
         "mean_ms": 1e9}]
    source["runtime"].setdefault("metadata", {})["tpot_mean_s"] = 1e9
    poisoned = tmp_path / "glm_poison.json"
    poisoned.write_text(json.dumps(source), encoding="utf-8")
    spec = z.CellSpec("glm_blind", "out", "decode", source_path,
                      "GLM-5.3/W8A8-MXFP8", 1024, 2, 8, 8, 1, 1, 1,
                      notes=("catalog:glm-5.3", "override_model"))
    clean = z.predict_cell(spec)
    dirty = z.predict_cell(z.replace(spec, model_case=poisoned))
    assert clean.layers == 78
    assert dirty.body_ms == pytest.approx(clean.body_ms)
    assert dirty.per_layer == clean.per_layer

def test_pipeline_parallel_stage_transfer_is_not_identical_to_pp1():
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen36_highconc_c4.json"
    spec = z.CellSpec("pp", "out", "decode", case, "Qwen3.6-27B",
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


def test_public_prediction_is_invariant_to_opaque_labels_and_suffixes():
    spec = z.CellSpec("qwen38_27b_dp4tp2_decode_1024_c1", "out", "decode",
                      MODEL_CASE, "Qwen3.8-27B", 1024, 1, 128, 2, 4, 1, 1,
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


def test_pp_prefill_uses_actual_hidden_rows_and_stage_link():
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
    base = z.CellSpec("pp_pf", "out", "prefill", case, "Qwen3.8-27B",
                      1024, 1, 1, 2, 4, 1, 1)
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


def test_pp_inter_node_placement_selects_roce_formula():
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
    spec = z.CellSpec("pp_inter", "out", "prefill", case, "Qwen3.8-27B",
                      1024, 1, 1, 8, 1, 1, 2)
    pred = z.predict_cell(spec)
    rows = [row for row in pred.rows if row.kind == "PP"]
    assert rows and "link_roce" in rows[0].formula


def test_native_glm51_source_config_changes_attention_and_body():
    store = Path("/Volumes/data/mindie-sim-data/a5/weights-metadata-20261108")
    glm51 = store / "GLM-5.1-w4a4c8-mxfp4" / "config.json"
    glm53 = store / "GLM-5.3-W8A8C8-mxfp8" / "config.json"
    if not glm51.is_file() or not glm53.is_file():
        pytest.skip("retained weights metadata store unavailable")
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm53flash_tp8_c4_p8k.json"
    base = z.CellSpec("glm51_dp16tp1ep16_dc_1k_c1", "out", "decode", case,
                      "GLM-5.1/W4A4C8", 1024, 1, 64, 1, 16, 16, 1)
    sha = lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    first = z.predict_cell(z.replace(base, source_config=glm51, source_config_sha256=sha(glm51), source_deploy_sha256=sha(glm51)))
    control = z.predict_cell(z.replace(base, source_config=glm53, source_config_sha256=sha(glm53), source_deploy_sha256=sha(glm53)))
    assert z.predict_cell(base).layers == 45  # old coarse GLM5.3 template
    assert first.layers == control.layers == 78
    raw51 = json.loads(glm51.read_text())["head_dim"]
    raw53 = json.loads(glm53.read_text())["head_dim"]
    assert (raw51, raw53) == (64, 192)
    assert first.body_ms != pytest.approx(control.body_ms)
    opaque = z.predict_cell(z.replace(base, source_config=glm51, source_config_sha256=sha(glm51),
                                      cell_id="opaque_l2_e8_k2", model_label="opaque"))
    assert opaque.layers == first.layers and opaque.body_ms == pytest.approx(first.body_ms)


def test_original_public_load_binds_glm51_and_glm53_native_architecture():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    cells = z.load_benchmark_jsonl(jsonl)
    found = {c.spec.cell_id: c for c in cells
             if c.spec.cell_id in {"glm51_dp16tp1ep16_dc_1k_c1",
                                   "glm53_dp16tp1ep16_dc_1k_c1"}}
    assert set(found) == {"glm51_dp16tp1ep16_dc_1k_c1",
                          "glm53_dp16tp1ep16_dc_1k_c1"}
    first = z.predict_cell(found["glm51_dp16tp1ep16_dc_1k_c1"].spec)
    control = z.predict_cell(found["glm53_dp16tp1ep16_dc_1k_c1"].spec)
    assert first.layers == control.layers == 78
    assert found["glm51_dp16tp1ep16_dc_1k_c1"].spec.source_config_sha256.startswith("726e45e2")
    assert found["glm53_dp16tp1ep16_dc_1k_c1"].spec.source_config_sha256.startswith("ca8f2f47")
    assert first.body_ms != pytest.approx(control.body_ms)


def test_pp2_decode_transfer_is_in_phase_body_and_service_once():
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
    base = z.CellSpec("pp_dc", "out", "decode", case, "Qwen3.8-27B",
                      1024, 1, 128, 2, 4, 1, 1)
    pp1 = z.predict_cell(base)
    pp2 = z.predict_cell(z.replace(base, pp=2))
    transfer = sum(row.duration_ms for row in pp2.rows if row.kind == "PP")
    assert transfer > 0.0
    assert pp2.body_ms == pytest.approx(pp1.body_ms + transfer)
    assert pp2.decode_body_ms == pytest.approx(pp2.body_ms)
    assert z._phase_body(pp2, "decode") == pytest.approx(pp2.body_ms)
    assert z._phase_body(pp1, "decode") == pytest.approx(pp1.body_ms)


def test_missing_or_wrong_deploy_identity_is_rejected_without_template():
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm53flash_tp8_c4_p8k.json"
    base = z.CellSpec("glm51_dp16tp1ep16_dc_1k_c1", "out", "decode", case,
                      "GLM-5.1/W4A4C8", 1024, 1, 64, 1, 16, 16, 1,
                      require_source=True)
    missing = z.predict_cell(base)
    assert missing.layers == 0 and "deploy_identity_missing_or_mismatch" in missing.notes
    store = Path("/Volumes/data/mindie-sim-data/a5/weights-metadata-20261108")
    glm51 = store / "GLM-5.1-w4a4c8-mxfp4" / "config.json"
    glm53 = store / "GLM-5.3-W8A8C8-mxfp8" / "config.json"
    if not glm51.is_file() or not glm53.is_file():
        pytest.skip("retained weights metadata store unavailable")
    sha = lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    wrong = z.predict_cell(z.replace(
        base, source_config=glm53, source_config_sha256=sha(glm53),
        source_deploy_sha256=sha(glm51)))
    assert wrong.layers == 0 and "deploy_identity_missing_or_mismatch" in wrong.notes


def test_pp2_decode_service_includes_prefill_transfer_not_only_body(monkeypatch):
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
    base = z.CellSpec("pp_dc_service", "out", "decode", case, "Qwen3.8-27B",
                      4096, 1, 64, 2, 4, 1, 1)
    monkeypatch.setattr(z, "_max_batched_tokens", lambda spec: 1024)
    pp1 = z.predict_cell(base)
    pp2 = z.predict_cell(z.replace(base, pp=2))
    decode_transfer = sum(row.duration_ms for row in pp2.rows if row.kind == "PP" and row.name.endswith(":c1") and row.name.startswith("pp_transfer:s0->8:c1"))
    assert pp2.body_ms == pytest.approx(pp1.body_ms + decode_transfer)
    assert pp2.ttft_ms > pp1.ttft_ms + decode_transfer


def test_pp_prefill_multi_chunk_transfer_startups(monkeypatch):
    case = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"
    spec = z.CellSpec("pp_pf_chunks", "out", "prefill", case, "Qwen3.8-27B",
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


def test_ordinary_pf32768c1_uses_exact_cohort_8192_chunks_and_pp_startups():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    cells = {c.spec.cell_id: c for c in z.load_benchmark_jsonl(jsonl)}
    cell = cells["qwen38_27b_dp4tp2_prefill_32768_c1"]
    assert cell.spec.source_case_dir is not None
    assert z._cohort_case(cell.spec).name == "qwen38_27b_dp4tp2.json"
    assert [g.requests[0].q_len for g in z._prefill_chunk_geometries(cell.spec)] == [8192] * 4
    pp1 = z.predict_cell(z.replace(cell.spec, pp=1))
    pp2 = z.predict_cell(z.replace(cell.spec, pp=2))
    rows = [row for row in pp2.rows if row.kind == "PP"]
    assert [row.name for row in rows] == [f"pp_transfer:s0->8:c{i}" for i in range(1, 5)]
    assert sum(row.duration_ms for row in rows) == pytest.approx(1.86549376)
    assert pp2.body_ms > 0 and pp1.body_ms > 0
    assert not [row for row in pp1.rows if row.kind == "PP"]


def test_distinct_declared_max_tokens_controls_chunk_count(tmp_path):
    case_dir = tmp_path / "out" / "qwen_probe"
    case_dir.mkdir(parents=True)
    cases = tmp_path / "cases"
    cases.mkdir(parents=True)
    (cases / "qwen_probe.json").write_text(json.dumps({
        "tp": 2, "dp": 4, "max_num_batched_tokens": 4096}))
    spec = z.CellSpec("qwen_probe_pf_32768_c1", "out", "prefill", MODEL_CASE,
                      "Qwen3.8-27B", 32768, 1, 1, 2, 4, 1, 1,
                      source_case_dir=case_dir)
    chunks = z._prefill_chunk_geometries(spec)
    assert z._max_batched_tokens(spec) == 4096
    assert [g.requests[0].q_len for g in chunks] == [4096] * 8
    pp1 = z.predict_cell(z.replace(spec, pp=1))
    pp2 = z.predict_cell(z.replace(spec, pp=2))
    rows = [row for row in pp2.rows if row.kind == "PP"]
    assert len(rows) == 8
    assert pp2.body_ms > pp1.body_ms


def test_explicit_header_archive_binds_f32_norm_and_bf16_gate_kv_b():
    oracle = HEADER_ORACLE
    jsonl = ZERO_SHOT_JSONL
    if not oracle.is_file() or not jsonl.is_file():
        pytest.skip("retained real header archive unavailable")
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_pf_1k_c1")
    spec = z.replace(cell.spec, source_header_archive=oracle)
    raw = z._raw_case(spec)
    quant = raw["model"]["quant"]
    overrides = dict(quant["category_overrides"])
    assert "norm" not in overrides
    assert dict(quant["norm_storage"])["attn_norm"] == "F32"
    assert raw["runtime"]["metadata"]["checkpoint_storage_dtypes"]["norm"] == "F32"
    assert dict(overrides["router"])["weight_format"] == "bf16"
    assert dict(overrides["mla.kv_b"])["weight_format"] == "bf16"
    assert dict(overrides["routed_expert"])["weight_format"] == "mxfp4"


def test_configured_provenance_root_applies_to_ordinary_json(monkeypatch):
    root = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not root.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    monkeypatch.setenv("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT", str(root))
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_pf_1k_c1")
    raw = z._raw_case(cell.spec)
    assert raw["runtime"]["metadata"]["checkpoint_storage_dtypes"]["norm"] == "F32"
    assert z._phase_body(z.predict_cell(cell.spec), "prefill") > 0


def test_explicit_archive_mismatch_preserves_scheme_kv_and_is_marked(monkeypatch):
    provenance = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not provenance.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_dc_1k_c1")
    correct = provenance / "GLM-5.1-w4a4c8-mxfp4.json"
    foreign = provenance / "GLM-5.3-W8A8C8-mxfp8.json"
    good = z.predict_cell(z.replace(cell.spec, source_header_archive=correct))
    bad = z.predict_cell(z.replace(cell.spec, source_header_archive=foreign))
    assert good.body_ms == pytest.approx(23.569564980218253)
    assert bad.body_ms == pytest.approx(27.983606186521286)
    assert "quant_source:header_source_ineligible:metadata_mismatch" in bad.notes
    assert z._raw_case(z.replace(cell.spec, source_header_archive=foreign))[
        "runtime"]["metadata"]["checkpoint_storage_dtypes"]["norm"] == "unknown"
    monkeypatch.setenv("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT", str(provenance))
    absent = z.predict_cell(z.replace(cell.spec, source_header_archive=Path("/never/absent.json")))
    assert "quant_source:header_source_unreadable:FileNotFoundError" in absent.notes
    assert z._raw_case(z.replace(cell.spec, source_header_archive=Path("/never/absent.json")))[
        "runtime"]["metadata"]["checkpoint_storage_dtypes"]["norm"] == "unknown"


def test_norm_storage_and_runtime_metadata_are_separate():
    provenance = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not provenance.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_dc_1k_c1")
    raw = z._raw_case(z.replace(
        cell.spec, source_header_archive=provenance / "GLM-5.1-w4a4c8-mxfp4.json"))
    meta = raw["runtime"]["metadata"]
    assert meta["norm_storage"]["attn_norm"] == "F32"
    assert meta["norm_runtime"] == {}
    assert meta["norm_storage_bytes"] == {"attn_norm": 24576}
    assert meta["norm_runtime_assumption"] == "bf16_default_assumption"


def test_public_cell_from_dict_preserves_missing_explicit_archive(monkeypatch):
    provenance = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not provenance.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    row = next(r for r in map(json.loads, jsonl.read_text().splitlines())
               if r["cell_id"] == "glm51_dp16tp1ep16_dc_1k_c1")
    monkeypatch.setenv("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT", str(provenance))
    cell = z.cell_from_dict({**row, "weight_header_archive": "/an/explicit/path-that-does-not-exist"})
    assert str(cell.spec.source_header_archive) == "/an/explicit/path-that-does-not-exist"
    pred = z.predict_cell(cell.spec)
    assert "quant_source:header_source_unreadable:FileNotFoundError" in pred.notes
    assert cell.spec.source_config_sha256.startswith("726e45e2")
    assert z._raw_case(cell.spec)["runtime"]["metadata"]["checkpoint_storage_dtypes"]["norm"] == "unknown"


def test_norm_facts_only_for_proven_roles_not_generic_hidden_size(monkeypatch):
    provenance = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not provenance.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    monkeypatch.delenv("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT", raising=False)
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_dc_1k_c1")
    no_header = z._raw_case(cell.spec)["runtime"]["metadata"]
    assert no_header.get("norm_storage", {}) == {} and no_header.get("norm_storage_bytes", {}) == {}
    with_header = z._raw_case(z.replace(
        cell.spec, source_header_archive=provenance / "GLM-5.1-w4a4c8-mxfp4.json"))
    quant = with_header["model"]["quant"]
    assert dict(quant["norm_storage"])["attn_norm"] == "F32"
    assert dict(quant["norm_runtime"]) == {}
    assert with_header["runtime"]["metadata"]["norm_storage_bytes"] == {"attn_norm": 24576}


def test_quant_spec_consumes_norm_storage_and_runtime_separately():
    provenance = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not provenance.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    from mindie_sim.prediction.structure import parse_case
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_dc_1k_c1")
    raw = z._raw_case(z.replace(
        cell.spec, source_header_archive=provenance / "GLM-5.1-w4a4c8-mxfp4.json"))
    quant = parse_case(raw).model.quant
    assert quant.norm_gamma_format("attn_norm") == "bf16"
    assert quant.norm_gamma_format("attn_norm", source=True) == "fp32"
    assert quant.norm_gamma_bytes(6144, "attn_norm") == 12288.0
    assert quant.norm_gamma_bytes(6144, "attn_norm", source=True) == 24576.0


def test_public_norm_runtime_abi_is_opt_in_and_source_config_scoped():
    provenance = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not provenance.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    row = next(r for r in map(json.loads, jsonl.read_text().splitlines())
               if r["cell_id"] == "glm51_dp16tp1ep16_dc_1k_c1")
    base = z.cell_from_dict(row).spec
    payload = {**row, "source_config": str(base.source_config),
               "source_config_sha256": base.source_config_sha256,
               "weight_header_archive": str(provenance / "GLM-5.1-w4a4c8-mxfp4.json")}
    without = z._raw_case(z.cell_from_dict(payload).spec)["runtime"]["metadata"]
    with_abi = z._raw_case(z.cell_from_dict(
        {**payload, "norm_runtime_abi": {"attn_norm": "BF16"}}).spec)["runtime"]["metadata"]
    assert without["norm_runtime"] == {} and without["norm_runtime_bytes"] == {}
    assert with_abi["norm_runtime"] == {"attn_norm": "BF16"}
    assert with_abi["norm_runtime_bytes"] == {"attn_norm": 12288}
    assert with_abi["norm_storage_bytes"] == {"attn_norm": 24576}


def test_original_glm_source_model_fields_and_index_dtype_are_bound():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    from mindie_sim.prediction.structure import parse_case
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_pf_1k_c1")
    raw = z._raw_case(cell.spec)
    model = parse_case(raw).model
    plan = model.layer_plans[3]
    assert (model.layers, model.hidden_size) == (78, 6144)
    assert (plan.q_lora_rank, plan.kv_lora_rank) == (2048, 512)
    assert (plan.qk_nope_head_dim, plan.qk_rope_head_dim, plan.v_head_dim) == (192, 64, 256)
    assert (plan.num_heads, plan.num_experts, plan.top_k) == (64, 256, 8)
    assert (plan.index_heads, plan.index_dim, plan.index_topk) == (32, 128, 2048)
    assert (model.quant.kv_dtype, model.quant.index_dtype) == ("fp8_e4m3", "fp8_e4m3")
    assert raw["runtime"]["metadata"].get("template_metadata")


def test_glm_source_indexer_roles_are_fp8_bf16_bf16(monkeypatch):
    provenance = PROVENANCE_ROOT
    jsonl = ZERO_SHOT_JSONL
    if not provenance.is_dir() or not jsonl.is_file():
        pytest.skip("retained W3 provenance unavailable")
    monkeypatch.setenv("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT", str(provenance))
    from mindie_sim.prediction.structure import parse_case
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "glm51_dp16tp1ep16_pf_1k_c1")
    raw = z._raw_case(cell.spec)
    quant = parse_case(raw).model.quant
    assert quant.format_for("indexer") == "fp8_e4m3"
    assert quant.format_for("indexer.pool_projection") == "bf16"
    assert quant.format_for("indexer.weights") == "bf16"
    pred = z.predict_cell(cell.spec)
    rows = {row.name: row.duration_ms for row in pred.rows}
    assert rows["index_q_projection"] == pytest.approx(0.115178, rel=1e-4)
    assert rows["index_k_projection"] == pytest.approx(0.032527, rel=1e-4)
    assert rows["index_weights_projection"] == pytest.approx(0.016401, rel=1e-4)


def test_indexer_override_rejects_arbitrary_and_nonphysical_roles():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    row = next(r for r in map(json.loads, jsonl.read_text().splitlines())
               if r["cell_id"] == "glm51_dp16tp1ep16_pf_1k_c1")
    for declared in ({"routed_expert": "BF16"}, {"indexer.weights": "F32"}):
        pred = z.predict_cell(z.cell_from_dict(
            {**row, "indexer_weight_formats": declared}).spec)
        assert pred.layers == 0
        assert any(note.startswith("quant_role_error:indexer_weight_format_unsupported")
                   for note in pred.notes)


def test_dsv41_authentic_bf16_indexer_roles_reach_normal_quant():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    from mindie_sim.prediction.structure import parse_case
    row = next(r for r in map(json.loads, jsonl.read_text().splitlines())
               if r["cell_id"] == "dsv41_dp16tp1ep16_dc_128k_c1")
    cell = z.cell_from_dict({**row, "indexer_weight_formats": {
        "indexer.pool_projection": "BF16", "indexer.weights": "BF16"}})
    quant = parse_case(z._raw_case(cell.spec)).model.quant
    assert quant.format_for("indexer") == "fp8_e4m3"
    assert quant.format_for("indexer.pool_projection") == "bf16"
    assert quant.format_for("indexer.weights") == "bf16"
    assert quant.format_for("routed_expert") == "mxfp4"


def test_ds_role_declaration_changes_only_two_indexer_categories():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    from mindie_sim.prediction.structure import parse_case
    row = next(r for r in map(json.loads, jsonl.read_text().splitlines())
               if r["cell_id"] == "dsv41_dp16tp1ep16_pf_1k_c1")
    base = z.cell_from_dict(row)
    declared = z.cell_from_dict({**row, "indexer_weight_formats": {
        "indexer.pool_projection": "BF16", "indexer.weights": "BF16"}})
    q0 = parse_case(z._raw_case(base.spec)).model.quant
    q1 = parse_case(z._raw_case(declared.spec)).model.quant
    changed = {cat for cat, _ in q1.category_overrides} - {cat for cat, _ in q0.category_overrides}
    assert changed == {"indexer.pool_projection", "indexer.weights"}
    assert (q1.kv_dtype, q1.index_dtype) == (q0.kv_dtype, q0.index_dtype) == ("bf16", "int8")
    meta = z._raw_case(declared.spec)["runtime"]["metadata"]
    assert meta["checkpoint_storage_dtypes"] == {}
    assert meta["indexer_runtime_formats"] == {
        "indexer.pool_projection": "BF16", "indexer.weights": "BF16"}
    assert meta["indexer_weight_formats"] == {
        "indexer.pool_projection": "unknown", "indexer.weights": "unknown"}


def test_qwen36_preserves_declared_w8a8_quant_and_gdn_bf16_roles():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    from mindie_sim.prediction.structure import parse_case
    cell = next(c for c in z.load_benchmark_jsonl(jsonl)
                if c.spec.cell_id == "smoke_qwen36_single_pf_4k_c1")
    raw = z._raw_case(cell.spec)
    assert raw["model"]["quantization"] == "w8a8_dynamic"
    assert "quant" in raw["model"]
    model = parse_case(raw).model
    assert (model.layers, model.hidden_size) == (64, 5120)
    assert (model.quant.weight_format, model.quant.activation_format) == ("int8", "int8")
    assert model.quant.format_for("gdn.o") == "bf16"
    assert model.quant.format_for("gdn.beta_alpha") == "bf16"
    assert model.quant.format_for("dense_mlp") == "int8"
    assert model.quant.format_for("lm_head") == "bf16"
    assert (model.quant.runtime_weight_scale_format, model.quant.runtime_weight_scale_bytes) == ("bf16", 2.0)
    assert (model.quant.runtime_activation_scale_format, model.quant.runtime_int8_weight_metadata) == ("fp32", "scale_only")
    pred = z.predict_cell(cell.spec)
    gate = [row for row in pred.rows if row.name == "gate_up"][0]
    assert "34816" in gate.formula and "69632" not in gate.formula
    assert pred.body_ms == pytest.approx(367.3606869373409)


def test_qwen36_foreign_glm_template_quant_is_rejected():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    row = next(r for r in map(json.loads, jsonl.read_text().splitlines())
               if r["cell_id"] == "smoke_qwen36_single_pf_4k_c1")
    cell = z.cell_from_dict({**row, "model_case":
        str(ROOT / "examples" / "structure" / "cases" /
            "decode-a5_glm53flash_tp8_c4_p8k.json")})
    raw = z._raw_case(cell.spec)
    assert raw["model"].keys() == {"hf_config"}
    assert raw["runtime"]["metadata"]["template_quant_authority"] in {"foreign_family_rejected", "cross_version_template_rejected"}
    assert z.predict_cell(cell.spec).body_ms == pytest.approx(503.51347702374693)


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


def test_qwen36_same_family_template_is_conditional_and_checkpoint_unbound():
    jsonl = ZERO_SHOT_JSONL
    if not jsonl.is_file():
        pytest.skip("retained original 731 jsonl unavailable")
    row = next(r for r in map(json.loads, jsonl.read_text().splitlines())
               if r["cell_id"] == "smoke_qwen36_single_pf_4k_c1")
    raw = z._raw_case(z.cell_from_dict(row).spec)
    assert raw["runtime"]["metadata"]["template_quant_authority"] == "same_family_template_conditional"
    source = raw["model"]["quant"]["source"]
    assert source["checkpoint_binding"] == "not_verified_from_source"
    assert "checkpoint" not in source
