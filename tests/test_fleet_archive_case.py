"""Structural archive-case mapping for DSH, Wave 5, and extended captures.

The mapper returns None outside those suites. Inside the domain it joins the
registry case path to receipt geometry by source SHA. It does not copy service
regimes, device rates, row timings, or a template parallel that disagrees.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_STRUCTURE = ROOT / "examples" / "structure"
if str(_STRUCTURE) not in sys.path:
    sys.path.insert(0, str(_STRUCTURE))

import fleet_archive_case as archive  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _template() -> dict:
    return {
        "name": "demo-template",
        "machine": {
            "backend": "ascend", "sku": "Ascend910B4", "num_devices": 8, "ranks_per_node": 8,
            "device": {"rates": {"native_call_service": 1.0}, "resource_units": {"native_call_service": 1},
                       "work_units": {"native_call_service": "busy_ns"}},
        },
        "model": {
            "name": "deepseek-v2-lite",
            "hf_config": {"model_type": "deepseek_v2", "num_hidden_layers": 27, "hidden_size": 2048,
                          "vocab_size": 102400, "n_routed_experts": 64, "num_experts_per_tok": 6},
        },
        "workload": {"num_requests": 1, "prompt_tokens": 4096, "output_tokens": 160},
        "runtime": {
            "tp": 8, "dp": 1, "ep": 8, "pp": 1, "max_num_seqs": 16, "graph_buckets": [1, 2, 4],
            "kernels": {"service_regimes": [{"id": "fit", "response": {"fixed_us": 12.5}}],
                        "lowerings": {"attention": {"kind": "declared"}}},
            "metadata": {"calibration_origin": "observed", "evaluation_relation": "in_sample", "speculation": {"enabled": False}},
        },
    }


def _receipt(source: Path, *, layers=27, tp=4, query=1, sequences=1, tokens=1) -> dict:
    return {
        "cache_version": "v-test", "parser_identity": "parser-test",
        "observed": {
            "phase": "decode",
            "source_identity": {"path": str(source), "sha256": _sha(source), "size_bytes": source.stat().st_size},
            "model_declaration": {"name": "deepseek-v2-lite", "layers": layers, "hidden_size": 2048,
                                  "vocab_size": 102400, "tp": tp},
            "geometry_groups": [{
                "geometry": {"query_rows": query, "sequences_per_replica": sequences, "tokens_per_sequence": tokens,
                             "context_tokens": None, "context_basis": "not_observed_from_cache_capacity",
                             "batch_basis": "captured_paged_attention_block_table_rows"},
                "rank_id": "0", "device_id": "0", "forward_ids": ["a", "b"],
                "body_forward_span_ms": {"mean": 999.0},
            }],
        },
    }


def _layout(tmp_path: Path, *, layers=27, receipt_tp=4, registry_tp=4, path_tp=4, second_query=None):
    source = tmp_path / "data" / "a2" / "heldout_engine_20261031" / f"a2_real_dsv2lite_E64_K6_tp{path_tp}ep4_decode_128k_c1" / "kernel_details.csv"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"Name,Duration\nAdd,1\n")
    cases = tmp_path / "cases"
    _write(cases / "a2-dsv2lite-w8a8-tp4ep4.json", _template())
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    _write(receipt, _receipt(source, layers=layers, tp=receipt_tp))
    if second_query is not None:
        other = tmp_path / "extractions" / ("b" * 64 + ".json")
        _write(other, _receipt(source, layers=layers, tp=receipt_tp, query=second_query))
    else:
        other = None
    pred = tmp_path / "extractions" / ("pred_" + "c" * 64 + ".json")
    _write(pred, {"observed_ms": 1, "observed": {"source_identity": {"path": str(source), "sha256": "0" * 64}}})
    cohort = "a2/a2_real_dsv2lite_E64_K6_tp4ep4_decode"
    cell = source.parent.name
    record = {
        "path": str(source), "hw": "a2", "cohort": cohort, "cell": cell, "family": "deepseek-v2-lite",
        "phase": "decode", "tp": registry_tp, "dp": 1, "ep": 4, "num_layers": layers, "num_experts": 64,
        "top_k": 6, "template": "a2-dsv2lite-w8a8-tp4ep4.json", "observed_ms": 18.0, "predicted_ms": 19.0,
        "relative_error": 0.05,
    }
    results = tmp_path / "results"
    _write(results / "wave5_full_generalization.json", {
        "schema_version": "mindie-wave5-full-generalization/1",
        "sim_identity": "mindie_sim/test", "parser_identity": "mindie_profiler/test",
        "chip_report_identities": {"a2": {"schema_version": "chip", "sim_identity": "mindie_sim/test", "parser_identity": "mindie_profiler/test"}},
        "cohort_summaries": [{"cohort": cohort, "calibration_provenance": {
            "evaluation_relation": "in_sample_regime_calibration", "target_timing_used_to_fit": True,
            "heldout_observed_values_used_in_fit": True}}],
        "cases": [record],
    })
    _write(results / "dsh_full_generalization.json", {"schema_version": "mindie-dsh-full-generalization/2", "heldout_cases": []})
    lines = ["source_path\treceipt\n", f"{source}\t{receipt}\n"]
    if other is not None:
        lines.append(f"{source}\t{other}\n")
    lines.append(f"{source}\t{pred}\n")
    index = tmp_path / "receipts.tsv"
    index.write_text("".join(lines), encoding="utf-8")
    archive.configure_archive_roots(
        data_roots=(tmp_path / "data",), results_dir=results, cases_dir=cases,
        archive_root=tmp_path / "missing-archive", receipt_index=index, cases_index=tmp_path / "no-cases.json",
    )
    return source


def _row(source: Path, **overrides):
    cell = source.parent.name
    cohort = "a2/a2_real_dsv2lite_E64_K6_tp4ep4_decode"
    row = {
        "suite": "wave5_20261031", "capture_id": f"wave5:a2:{cohort}:{cell}", "phase": "decode",
        "hardware_tier": "A2", "model_case": "stale-tp8.json", "observed_ms": 12345.6, "predicted_ms": 1.0,
        "geometry": {"tp": 99, "context_tokens": 999999, "structural_weights": [1, 0], "active_hbm_mb": 4},
        "source_calibration": {"evaluation_relation": "zero_shot_piecewise_recomputed", "target_timing_used_to_fit": False},
    }
    row.update(overrides)
    return row


def test_outside_domain_is_none(tmp_path):
    _layout(tmp_path)
    assert archive.resolve_archive_case({"suite": "a5_multinode_full_coverage_20261108", "capture_id": "a5_multinode_20261108:x"}) is None
    assert archive.resolve_archive_case({"suite": "registered_decode", "capture_id": "registered_decode:glm"}) is None
    assert archive.resolve_archive_case(None) is None


def test_stale_template_parallel_is_not_applied(tmp_path):
    source = _layout(tmp_path)
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "resolved"
    assert result["case"]["runtime"]["tp"] == 4
    assert result["case"]["runtime"]["ep"] == 4
    assert result["case"]["runtime"]["dp"] == 1
    assert result["provenance"]["template_parallel"] == {"tp": 8, "dp": 1, "ep": 8}
    assert result["provenance"]["template_parallel_conflict"] is True
    assert result["provenance"]["stale_scheduler_not_applied"]["max_num_seqs"] == 16
    assert "graph_buckets" not in result["case"]["runtime"]
    kernels = result["case"]["runtime"].get("kernels") or {}
    assert "service_regimes" not in kernels
    assert kernels.get("lowerings", {}).get("attention", {}).get("kind") == "declared"
    assert "rates" not in (result["case"]["machine"].get("device") or {})
    assert "calibration_origin" not in (result["case"]["runtime"].get("metadata") or {})
    assert result["case"]["workload"] is None
    assert result["case_ready_for_parse"] is False
    assert result["predictable"] is False
    assert "context_tokens" in result["geometry"]["missing"]
    assert result["geometry"]["populations"][0]["context_tokens"] is None
    assert result["geometry"]["populations"][0]["forward_count"] == 2
    assert result["geometry"]["populations"][0]["sequences_per_replica"] == 1
    assert result["provenance"]["evaluation_relation"] == "in_sample_regime_calibration"
    assert result["provenance"]["holdout_independent"] is False
    assert result["provenance"]["generator_revision"]["sim_identity"] == "mindie_sim/test"
    assert result["source"]["sha256_verified"] is True
    assert result["case"]["model"]["hf_config"]["num_hidden_layers"] == 27
    assert result["case"]["model"]["num_experts"] == 64
    assert result["case"]["machine"]["num_devices"] == 4


def test_row_timing_and_geometry_do_not_change_the_case(tmp_path):
    source = _layout(tmp_path)
    base = archive.resolve_archive_case(_row(source))
    mutated = _row(source)
    mutated["observed_ms"] = 0.001
    mutated["predicted_ms"] = 1e9
    mutated["geometry"] = {"context_tokens": 1, "structural_weights": [0], "active_hbm_mb": 0, "tp": 1, "sequences_per_replica": 32}
    again = archive.resolve_archive_case(mutated)
    assert again["case"] == base["case"]
    assert again["geometry"]["populations"] == base["geometry"]["populations"]
    assert again["provenance"]["evaluation_relation"] == base["provenance"]["evaluation_relation"]


def test_disagreeing_receipts_are_a_conflict(tmp_path):
    source = _layout(tmp_path, second_query=4)
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "conflict"
    assert result["case"] is None
    assert "receipt_structural_signature_disagrees" in result["diagnostics"]


def test_receipt_parallel_conflict_is_not_averaged(tmp_path):
    source = _layout(tmp_path, receipt_tp=8, registry_tp=4, path_tp=4)
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "conflict"
    assert result["case"] is None
    assert any(item.startswith("conflict:tp") for item in result["diagnostics"])


def test_reduced_depth_is_not_relabelled_as_the_template_depth(tmp_path):
    source = _layout(tmp_path, layers=8)
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "resolved"
    assert result["case"]["model"]["layers"] == 8
    assert result["case"]["model"]["hf_config"]["num_hidden_layers"] == 8
    assert "catalog_key" not in result["case"]["model"]
    assert result["case"]["model"]["metadata"]["not_full_catalog_depth"] is True
    assert result["case"]["model"]["name"] == "deepseek-v2-lite"


def test_source_sha_mismatch_stays_unresolved(tmp_path):
    source = _layout(tmp_path)
    source.write_bytes(b"Name,Duration\nAdd,2\n")
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "insufficient_evidence"
    assert result["case"] is None
    assert any(item.startswith("source_sha256_mismatch") for item in result["diagnostics"])


def test_extended_alias_keeps_its_id_and_blocks_holdout(tmp_path):
    source = _layout(tmp_path)
    rel = source.parent.relative_to(tmp_path / "data").as_posix()
    row = {
        "suite": "extended_a3_a5_workstream_captures",
        "capture_id": f"extended_a3_a5_workstream_captures:{rel}",
        "phase": "decode", "hardware_tier": "A2", "model_case": "heldout_engine_20261031",
        "source_calibration": {"evaluation_relation": "zero_shot_piecewise_recomputed"},
        "observed_ms": 50,
    }
    result = archive.resolve_archive_case(row)
    assert result["status"] == "resolved"
    assert result["capture_id"] == row["capture_id"]
    assert result["provenance"]["alias_of"][0]["suite"] == "wave5_20261031"
    assert result["provenance"]["evaluation_relation"] == "in_sample_regime_calibration"
    assert result["provenance"]["holdout_independent"] is False
    assert result["case"]["runtime"]["tp"] == 4


def test_extended_without_declaration_is_not_invented(tmp_path):
    _layout(tmp_path)
    orphan = tmp_path / "data" / "a2" / "orphan_cell" / "kernel_details.csv"
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(b"Name\n")
    row = {"suite": "extended_a3_a5_workstream_captures", "capture_id": "extended_a3_a5_workstream_captures:a2/orphan_cell",
           "phase": "decode", "model_case": "orphan_cell"}
    result = archive.resolve_archive_case(row)
    assert result["status"] == "insufficient_evidence"
    assert result["case"] is None
    assert "extended_source_has_no_structural_declaration" in result["diagnostics"]


def _registered_row(tmp_path: Path, *, relation: str, case_ep: int = 4, path_ep: int | None = None,
                    gz: str | None = None, capture_suffix: str = ""):
    _layout(tmp_path)
    label = f"tp4ep{path_ep}_cell" if path_ep else "tp4_cell"
    cell = tmp_path / "data" / "a3" / "prof" / label
    csv = cell / "kernel_details.csv"
    csv.parent.mkdir(parents=True)
    raw = b"Name,Duration\nAdd,9\n"
    csv.write_bytes(raw)
    if gz == "same":
        (cell / "kernel_details.csv.gz").write_bytes(gzip.compress(raw))
    elif gz == "other":
        (cell / "kernel_details.csv.gz").write_bytes(gzip.compress(b"Name,Duration\nAdd,8\n"))
    model = tmp_path / "cases" / "reg-model.json"
    payload = _template()
    payload["runtime"]["tp"] = 4
    payload["runtime"]["dp"] = 1
    payload["runtime"]["ep"] = case_ep
    _write(model, payload)
    receipt = tmp_path / "extractions" / ("d" * 64 + ".json")
    _write(receipt, _receipt(csv, tp=4))
    _write(tmp_path / "cases.json", {"cases": [{
        "case_id": "reg-demo", "phase": "decode",
        "source": {"path": str(csv), "sha256": _sha(csv)},
        "model_declaration": {"path": str(model), "sha256": _sha(model)},
        "extraction_path": str(receipt),
        "calibration": {"evaluation_relation": relation},
    }]})
    archive.configure_archive_roots(
        data_roots=(tmp_path / "data",), results_dir=tmp_path / "results", cases_dir=tmp_path / "cases",
        archive_root=tmp_path / "missing-archive", receipt_index=tmp_path / "receipts.tsv",
        cases_index=tmp_path / "cases.json",
    )
    rel = csv.parent.relative_to(tmp_path / "data").as_posix() + capture_suffix
    return {
        "suite": "extended_a3_a5_workstream_captures",
        "capture_id": f"extended_a3_a5_workstream_captures:{rel}",
        "phase": "decode", "hardware_tier": "A2", "model_case": "ignored.json",
        "source_calibration": {"evaluation_relation": "zero_shot_piecewise_recomputed"},
    }


def test_matching_gzip_is_the_same_source_and_not_declared_is_not_holdout(tmp_path):
    row = _registered_row(tmp_path, relation="not_declared", gz="same")
    result = archive.resolve_archive_case(row)
    assert result["status"] == "resolved"
    assert result["capture_id"] == row["capture_id"]
    assert result["provenance"]["alias_of"][0]["capture_id"] == "reg-demo"
    assert result["provenance"]["evaluation_relation"] == "not_declared"
    assert result["provenance"]["holdout_independent"] is False
    assert result["case"]["runtime"]["ep"] == 4
    assert result["geometry"]["parallel"]["ep_from"] == ["registry"]
    assert result["case"]["runtime"]["tp"] == 4


def test_different_gzip_is_a_conflict(tmp_path):
    row = _registered_row(tmp_path, relation="not_declared", gz="other")
    result = archive.resolve_archive_case(row)
    assert result["status"] == "conflict"
    assert result["case"] is None
    assert "kernel_serializations_disagree" in result["diagnostics"]


def test_id_suffix_joins_the_same_kernel(tmp_path):
    row = _registered_row(tmp_path, relation="new_target_not_used_for_fitting", gz="same", capture_suffix="#2")
    result = archive.resolve_archive_case(row)
    assert result["status"] == "resolved"
    assert result["capture_id"].endswith("#2")
    assert result["provenance"]["holdout_independent"] is True
    assert result["provenance"]["alias_of"][0]["suite"] == "registered"


def test_path_ep_disagreement_is_not_taken_from_the_case(tmp_path):
    row = _registered_row(tmp_path, relation="new_target_not_used_for_fitting", case_ep=8, path_ep=4)
    result = archive.resolve_archive_case(row)
    assert result["status"] == "conflict"
    assert result["case"] is None
    assert any(item.startswith("conflict:ep") for item in result["diagnostics"])


def test_inspected_relation_blocks_holdout(tmp_path):
    row = _registered_row(tmp_path, relation="new_target_not_used_for_fitting; previously_inspected_not_blind")
    result = archive.resolve_archive_case(row)
    assert result["status"] == "resolved"
    assert result["provenance"]["holdout_independent"] is False
    assert "not_blind" in result["provenance"]["holdout_block_reason"]


def test_extended_sha_join_uses_the_receipt_digest(tmp_path):
    source = _layout(tmp_path)
    digest = _sha(source)
    index = tmp_path / "receipts.tsv"
    lines = index.read_text(encoding="utf-8").splitlines()
    rewritten = [lines[0] + "\tsource_sha256"]
    rewritten.extend(line + "\t" + digest for line in lines[1:])
    index.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    copy = tmp_path / "data" / "a2" / "relocated_cell" / "kernel_details.csv"
    copy.parent.mkdir(parents=True)
    copy.write_bytes(source.read_bytes())
    archive.clear_archive_caches()
    row = {
        "suite": "extended_a3_a5_workstream_captures",
        "capture_id": "extended_a3_a5_workstream_captures:a2/relocated_cell",
        "phase": "decode", "hardware_tier": "A2", "model_case": "ignored.json",
        "source_calibration": {"evaluation_relation": "zero_shot_piecewise_recomputed"},
    }
    result = archive.resolve_archive_case(row)
    assert result["status"] == "resolved"
    assert result["provenance"]["alias_of"][0]["suite"] == "wave5_20261031"
    assert result["provenance"]["holdout_independent"] is False
    assert result["source"]["sha256_verified"] is True
    assert result["capture_id"] == row["capture_id"]


def test_absent_receipt_name_does_not_reject_the_case(tmp_path):
    _layout(tmp_path)
    case = json.loads((tmp_path / "cases" / "a2-dsv2lite-w8a8-tp4ep4.json").read_text(encoding="utf-8"))
    declaration = {"layers": 27, "hidden_size": 2048, "vocab_size": 102400, "tp": 4}
    model, notes, _missing = archive._reconcile_model(
        case, declaration, "deepseek-v2-lite", {"num_experts": 64, "top_k": 6}, 27, 64, 6,
    )
    assert model["name"] == "deepseek-v2-lite"
    assert "receipt_model_name_absent" in notes


def test_catalog_experts_follow_the_captured_population(tmp_path):
    _layout(tmp_path)
    case = json.loads((tmp_path / "cases" / "a2-dsv2lite-w8a8-tp4ep4.json").read_text(encoding="utf-8"))
    case["model"]["hf_config"]["n_routed_experts"] = 384
    case["model"]["hf_config"]["num_experts_per_tok"] = 6
    declaration = {"name": "deepseek-v2-lite", "layers": 8, "hidden_size": 2048, "vocab_size": 102400, "tp": 4}
    model, notes, _missing = archive._reconcile_model(
        case, declaration, "deepseek-v2-lite", {"layers": 8, "num_experts": 16, "top_k": 4}, 8, 16, 4,
    )
    assert model["num_experts"] == 16
    assert model["top_k"] == 4
    assert model["layers"] == 8
    assert model["hf_config"]["n_routed_experts"] == 16
    assert model["hf_config"]["num_hidden_layers"] == 8
    assert model["metadata"]["not_full_catalog_experts"] is True
    assert not any(str(item).startswith("conflict:") for item in notes)


def test_conflicting_expert_counts_stay_a_conflict(tmp_path):
    source = _layout(tmp_path)
    document = json.loads((tmp_path / "results" / "wave5_full_generalization.json").read_text(encoding="utf-8"))
    document["cases"][0]["num_experts"] = 32
    (tmp_path / "results" / "wave5_full_generalization.json").write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "conflict"
    assert result["case"] is None
    assert any(item.startswith("conflict:num_experts") for item in result["diagnostics"])


def test_placeholder_qwen30_name_uses_the_family(tmp_path):
    declaration = {"name": "model", "layers": 8, "hidden_size": 2048, "vocab_size": 151936, "tp": 4}
    model, notes, _missing = archive._reconcile_model(
        None, declaration, "synth-qwen3-30b-a3b", {"layers": 8, "num_experts": 16, "top_k": 2}, 8, 16, 2,
    )
    assert model["name"] == "synth-qwen3-30b-a3b"
    assert model["layers"] == 8
    assert model["hidden_size"] == 2048
    assert "receipt_model_name_not_specific" in notes


def test_select_population_requires_one_structural_match(tmp_path):
    source = _layout(tmp_path)
    result = archive.resolve_archive_case(_row(source))
    assert archive.select_population(result, 1, 1)["forward_count"] == 2
    assert archive.select_population(result, 2, 1) is None
    assert archive.select_population(result, 1, 1)["context_tokens"] is None


def test_declared_client_is_priceable_without_copying_the_path_label(tmp_path):
    source = _layout(tmp_path)
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    document = json.loads(receipt.read_text(encoding="utf-8"))
    document["meta"] = {
        "client": {"input_len": 126000, "concurrency": 16, "output_tokens": 2048},
        "context_evidence": {
            "basis": "retained_request_prompt_usage", "representative_tokens": 126000,
            "lower_bound_tokens": 126000, "upper_bound_tokens": 128048,
            "per_step_context_observed": False, "client_token_exact": True,
        },
    }
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source))
    workload = result["case"]["workload"]
    assert result["status"] == "resolved"
    assert result["case_ready_for_parse"] is True
    assert result["predictable"] is True
    assert result["predictable_scope"] == "declared_service_request"
    assert workload["num_requests"] == 16
    assert workload["prompt_tokens"] == 126000
    assert workload["output_tokens"] == 2048
    assert "prefix_tokens" not in workload
    assert result["geometry"]["populations"][0]["context_tokens"] is None
    assert result["geometry"]["context"]["per_step_context_observed"] is False
    assert result["geometry"]["context"]["lower_bound_tokens"] == 126000
    assert result["geometry"]["context"]["upper_bound_tokens"] == 128048
    assert result["geometry"]["batch"]["global_concurrency"] == 16
    assert result["geometry"]["batch"]["local_sequences_per_replica"] == 1
    assert result["case"]["runtime"].get("max_model_len") != 126000
    assert "128k" not in json.dumps(workload)


def test_prefill_initial_cache_zero_is_a_context(tmp_path):
    source = _layout(tmp_path)
    source.write_text(
        "Name,Start Time(us),Input Shapes\n"
        "aclnnFusedInferAttentionScoreV3_FusedInferAttentionScore_FusedInferAttentionScore,10,\"4096,4,128;4096,4,128\"\n",
        encoding="utf-8",
    )
    summary = {
        "summary": {
            "concurrency": 1, "token_exact": True, "max_running": 1,
            "prefix": {"hits": 0, "queries": 4096, "cached_tokens": 0, "prompt_tokens": 4096},
            "design": {"prompt_tokens": 4096, "shared_tokens": 0, "fresh_tokens": 4096, "max_tokens": 1},
            "profile": {"start_profile_epoch": 10.0, "stop_profile_epoch": 12.0},
        },
        "requests": [{
            "idx": 0, "prompt_tokens": 4096, "completion_tokens": 1, "ok": True,
            "usage": {"prompt_tokens": 4096, "completion_tokens": 1, "total_tokens": 4097},
            "chunk_epochs": [11.0],
        }],
    }
    _write(source.parent / "benchmark_summary.json", summary)
    (source.parent / "meta.env").write_text("INPUT_LEN=4096\nPREFIX_LEN=0\nOUTPUT_LEN=1\nCONCURRENCY=1\nSPEC_K=0\nTP=4\nDP=1\nEP=4\n", encoding="utf-8")
    (source.parent / "cmd.sh").write_text(
        "vllm serve model --tensor-parallel-size 4 --data-parallel-size 1 --max-model-len 163840 "
        "--max-num-seqs 32 --max-num-batched-tokens 8192 --gpu-memory-utilization 0.88 --block-size 128 "
        "--enable-prefix-caching --enable-chunked-prefill\n",
        encoding="utf-8",
    )
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    document = json.loads(receipt.read_text(encoding="utf-8"))
    document["observed"]["phase"] = "prefill"
    document["observed"]["source_identity"]["sha256"] = _sha(source)
    document["observed"]["source_identity"]["size_bytes"] = source.stat().st_size
    document["observed"]["geometry_groups"][0]["geometry"]["query_rows"] = 4096
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source, phase="prefill"))
    assert result["status"] == "resolved", result["diagnostics"]
    assert result["geometry"]["populations"][0]["context_tokens"] == 0
    assert result["geometry"]["context"]["per_step_context_observed"] is True
    assert result["predictable_scope"] == "captured_forward"
    assert result["case"]["workload"]["requests"][0]["prompt_tokens"] == 4096
    assert result["case"]["workload"]["requests"][0]["prefix_tokens"] == 0
    assert result["case"]["workload"]["requests"][0]["output_tokens"] == 1
    assert result["case"]["runtime"]["max_model_len"] == 163840
    assert result["case"]["runtime"].get("graph_capture_mode") != "FULL_DECODE_ONLY"
    assert result["geometry"]["batch"]["local_sequences_per_replica"] == 1
    assert result["geometry"]["launch"]["spec_k"] == 0
    assert result["geometry"]["launch"]["speculative_config_emitted"] is False
    assert result["geometry"]["frames"][0]["query_rows"] == 4096
    assert result["geometry"]["frames"][0]["context_tokens"] == 0
    assert result["geometry"]["frames"][0]["phase"] == "prefill"
    assert result["geometry"]["service_request_separate_from_captured_forwards"] is False


def test_missing_receipt_index_reads_the_canonical_archive(tmp_path):
    source = _layout(tmp_path)
    archive_root = tmp_path / "archive"
    dest = archive_root / "dsh-full-generalization" / "extractions"
    dest.mkdir(parents=True)
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    (dest / receipt.name).write_bytes(receipt.read_bytes())
    archive.configure_archive_roots(
        data_roots=(tmp_path / "data",), results_dir=tmp_path / "results", cases_dir=tmp_path / "cases",
        archive_root=archive_root, receipt_index=tmp_path / "missing-index.tsv", cases_index=tmp_path / "no-cases.json",
    )
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "resolved"
    assert result["source"]["sha256_verified"] is True
    assert result["case"]["workload"] is None


def test_launch_table_keeps_dspark_sku_and_length_differences(tmp_path):
    script = tmp_path / "run_wave234_v2.sh"
    script.write_text(
        "start_server() {\n"
        "  if [ \"$spec_k\" -gt 0 ]; then\n"
        "    SPEC_ARGS=(--speculative-config \"{\\\"method\\\":\\\"dspark\\\",\\\"num_speculative_tokens\\\":${spec_k}}\")\n"
        "  fi\n"
        "  echo \"EP16 spec_k=$spec_k\"\n"
        "  vllm serve \"$MODEL\" --max-model-len 131072 --block-size 128 --gpu-memory-utilization 0.85 \\\n"
        "    --additional-config \"{\\\"enable_fused_mc2\\\":1,\\\"enable_shared_expert_dp\\\":true,\\\"enable_force_eplb\\\":true}\" \\\n"
        "    --enable-prefix-caching --compilation-config \"{\\\"cudagraph_mode\\\":\\\"FULL_DECODE_ONLY\\\"}\" \\\n"
        "    --hf-overrides \"{\\\"engram_layer_ids\\\":[]}\"\n"
        "}\n"
        "run_matrix_for_cfg() { for c in 4 8 16 32; do true; done }\n"
        "if start_server \"tp2dp8_ep16_dspark0\" 2 8 0 16 4096 true; then\n"
        "  run_matrix_for_cfg \"tp2dp8_ep16_dspark0\" 0 \"3840:4096:4k:512:3.5:3.0 125000:126000:128k:2048:8.0:4.0\"\n"
        "fi\n"
        "if start_server \"tp2dp8_ep16_dspark7\" 2 8 7 16 4096 true; then\n"
        "  run_matrix_for_cfg \"tp2dp8_ep16_dspark7\" 7 \"125000:126000:128k:2048:8.0:4.0\"\n"
        "fi\n"
        "if start_server \"tp4dp4_ep16_dspark7_noflashcomm\" 4 4 7 24 4096 false; then\n"
        "  run_matrix_for_cfg \"tp4dp4_ep16_dspark7_noflashcomm\" 7 \"125000:126000:128k:2048:8.0:4.0\"\n"
        "fi\n",
        encoding="utf-8",
    )
    import fleet_archive_producer as producer
    table = producer._launch_table(script)
    dspark0 = table["tp2dp8_ep16_dspark0_decode_128k_c16"]
    dspark7 = table["tp2dp8_ep16_dspark7_decode_128k_c16"]
    four_k = table["tp2dp8_ep16_dspark0_decode_4k_c16"]
    no_flash = table["tp4dp4_ep16_dspark7_noflashcomm_decode_128k_c16"]
    assert dspark0["input_len"] == 126000 and dspark0["prefix_len"] == 125000 and dspark0["output_len"] == 2048
    assert dspark0["spec_k"] == 0 and dspark0["speculative_config_emitted"] is False
    assert dspark0["graph_capture_mode"] == "FULL_DECODE_ONLY"
    assert dspark0["max_model_len"] == 131072 and dspark0["max_num_seqs"] == 16
    assert dspark0["flashcomm"] is True and dspark0["label"] == "128k"
    assert dspark7["spec_k"] == 7 and dspark7["speculative_config_emitted"] is True
    assert dspark7["input_len"] == 126000
    assert four_k["input_len"] == 4096 and four_k["prefix_len"] == 3840 and four_k["output_len"] == 512
    assert no_flash["flashcomm"] is False and no_flash["max_num_seqs"] == 24 and no_flash["tp"] == 4
    assert no_flash["input_len"] == dspark0["input_len"]


def test_prefill_chunk_markers_keep_each_context(tmp_path):
    source = _layout(tmp_path)
    source.write_text(
        "Name,Start Time(us),Input Shapes,Device_id\n"
        "aclnnInplaceZero_ZerosLikeAiCore_ZerosLike,10,5,0\n"
        "FusedInferAttentionScore,11,\"5,4,128;5,4,128\",0\n"
        "aclnnInplaceZero_ZerosLikeAiCore_ZerosLike,20,3,0\n"
        "FusedInferAttentionScore,21,\"3,4,128;8,4,128\",0\n",
        encoding="utf-8",
    )
    summary = {
        "summary": {"concurrency": 1, "token_exact": True, "prefix": {"cached_tokens": 0, "hits": 0, "queries": 8},
                    "design": {"prompt_tokens": 8, "shared_tokens": 0, "max_tokens": 1}},
        "requests": [{"idx": 0, "prompt_tokens": 8, "completion_tokens": 1, "ok": True, "chunk_epochs": [11.0]}],
    }
    _write(source.parent / "benchmark_summary.json", summary)
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    document = json.loads(receipt.read_text(encoding="utf-8"))
    document["observed"]["phase"] = "prefill"
    document["observed"]["source_identity"]["sha256"] = _sha(source)
    document["observed"]["source_identity"]["size_bytes"] = source.stat().st_size
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source, phase="prefill"))
    frames = result["geometry"]["frames"]
    assert result["status"] == "resolved", result["diagnostics"]
    assert [(item["query_rows"], item["context_tokens"]) for item in frames] == [(5, 0), (3, 5)]
    assert result["geometry"]["populations"][0]["context_tokens"] is None
    assert result["predictable_scope"] == "captured_forward"
    assert result["geometry"]["service_request_separate_from_captured_forwards"] is True
    assert result["case"]["workload"]["requests"][0]["prompt_tokens"] == 8


def test_decode_tail_ordinals_follow_the_completion_suffix(tmp_path):
    source = _layout(tmp_path)
    lines = ["Name,Start Time(us),Input Shapes,Device_id"]
    for index in range(4):
        lines.append(f"FusedInferAttentionScore,{index},\"1,8,128;1,8,128\",0")
        if index % 2 == 1:
            lines.append(f"ArgMaxV2,{index}.5,\"1\",0")
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {
        "summary": {"concurrency": 1, "token_exact": True, "prefix": {"cached_tokens": 0, "hits": 0, "queries": 0},
                    "design": {"prompt_tokens": 8, "shared_tokens": 0, "max_tokens": 4},
                    "profile": {"start_profile_epoch": 25.0, "stop_profile_epoch": 50.0}},
        "requests": [{"idx": 0, "prompt_tokens": 8, "completion_tokens": 4, "ok": True,
                      "chunk_epochs": [10.0, 20.0, 30.0, 40.0]}],
    }
    _write(source.parent / "benchmark_summary.json", summary)
    (source.parent / "meta.env").write_text("INPUT_LEN=8\nPREFIX_LEN=0\nOUTPUT_LEN=4\nCONCURRENCY=1\nSPEC_K=0\nNUM_LAYERS=2\nTP=4\nDP=1\nEP=4\n", encoding="utf-8")
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    document = json.loads(receipt.read_text(encoding="utf-8"))
    document["observed"]["source_identity"]["sha256"] = _sha(source)
    document["observed"]["source_identity"]["size_bytes"] = source.stat().st_size
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source))
    frames = result["geometry"]["frames"]
    assert result["status"] == "resolved", result["diagnostics"]
    assert [(item["forward_id"], item["output_ordinal"], item["context_tokens"], item["query_rows"]) for item in frames] == [
        (2, 3, 9, 1), (3, 4, 10, 1),
    ]
    assert result["geometry"]["context"]["lower_bound_tokens"] == 9
    assert result["geometry"]["context"]["upper_bound_tokens"] == 10
    assert result["geometry"]["populations"][0]["context_tokens"] is None
    assert "128k" not in json.dumps(result["case"]["workload"])


def _qwen_output_files(source: Path, output: int) -> None:
    _write(source.parent / "benchmark_summary.json", {
        "summary": {"concurrency": 1, "token_exact": True, "prefix": {"cached_tokens": 0, "hits": 0, "queries": 0},
                    "design": {"prompt_tokens": 4096, "shared_tokens": 3968, "max_tokens": output}},
        "requests": [{"idx": 0, "prompt_tokens": 4096, "completion_tokens": output, "ok": True, "chunk_epochs": [1.0]}],
    })
    (source.parent / "meta.env").write_text(
        f"INPUT_LEN=4096\nOUTPUT_LEN={output}\nPREFIX_LEN=3968\nCONCURRENCY=1\nSPEC_K=0\nNPU_TYPE=Ascend950PR_A5\n",
        encoding="utf-8",
    )
    _write(source.parent / "run_meta.json", {
        "npu_type": "Ascend950PR_A5", "host": "177.31.22.1",
        "workload": {"input_len": 4096, "output_len": output},
    })


def test_exporter_output_placeholder_does_not_vote_against_raw_completion(tmp_path):
    source = _layout(tmp_path)
    _qwen_output_files(source, 256)
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    document = json.loads(receipt.read_text(encoding="utf-8"))
    document["meta"] = {
        "client": {"input_len": 4096, "concurrency": 1, "output_tokens": 192},
        "context_evidence": {"basis": "run_meta_workload_input_len", "representative_tokens": 4096},
    }
    document["observed"]["source_identity"]["sha256"] = _sha(source)
    document["observed"]["source_identity"]["size_bytes"] = source.stat().st_size
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "resolved", result["diagnostics"]
    assert "receipt_client_output_tokens_placeholder:192:eval_a5_wave5.extract_or_load" in result["diagnostics"]
    assert not any(str(item).startswith("conflict:output_tokens") for item in result["diagnostics"])
    assert result["case"]["workload"]["requests"][0]["output_tokens"] == 256
    assert result["case"]["workload"]["requests"][0]["prompt_tokens"] == 4096
    assert result["case"]["machine"]["sku"] == "Ascend950PR_9579"
    assert "hardware_sku_declared_not_serial_verified" in result["diagnostics"]
    assert "hardware_sku_conditional_not_exact" not in result["diagnostics"]
    candidates = result["geometry"]["hardware_candidates"]
    assert [item["declared_identity"] for item in candidates] == ["Ascend950PR_A5", "Ascend910B4"]
    assert candidates[0]["catalog_sku"] == "Ascend950PR_9579"
    assert candidates[0]["role"] == "producer_deployment_setting" and candidates[0]["priority"] == 1
    assert candidates[0]["applied"] is True
    assert candidates[0]["exact"] is False and candidates[0]["equipment_proof"] is None
    assert candidates[1]["applied"] is False and candidates[1]["role"] == "contrary_template"
    assert candidates[1]["exact"] is False and candidates[1]["source"] == "template_machine.sku"
    document["meta"]["context_evidence"]["basis"] = "retained_request_prompt_usage"
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    voted = archive.resolve_archive_case(_row(source))
    assert voted["status"] == "conflict"
    assert any("receipt_client=192" in str(item) and "usage=256" in str(item) for item in voted["diagnostics"])
    assert "receipt_client_output_tokens_placeholder:192:eval_a5_wave5.extract_or_load" not in voted["diagnostics"]
    _qwen_output_files(source, 192)
    document["meta"]["context_evidence"]["basis"] = "run_meta_workload_input_len"
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    same = archive.resolve_archive_case(_row(source))
    assert same["status"] == "resolved", same["diagnostics"]
    assert "receipt_client_output_tokens_placeholder:192:eval_a5_wave5.extract_or_load" in same["diagnostics"]
    assert same["case"]["workload"]["requests"][0]["output_tokens"] == 192


def test_receipt_windows_graph_bucket_and_conditional_scenarios(tmp_path):
    source = _layout(tmp_path)
    lines = ["Name,Start Time(us),Input Shapes,Device_id"]
    for index in range(4):
        lines.append(f"FusedInferAttentionScore,{index},\"1,8,128;1,8,128\",0")
        if index % 2 == 1:
            lines.append(f"ArgMaxV2,{index}.5,\"1\",0")
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write(source.parent / "benchmark_summary.json", {
        "summary": {"concurrency": 1, "token_exact": True, "prefix": {"cached_tokens": 0, "hits": 0, "queries": 0},
                    "design": {"prompt_tokens": 8, "shared_tokens": 0, "max_tokens": 4},
                    "profile": {"start_profile_epoch": 25.0, "stop_profile_epoch": 50.0}},
        "requests": [{"idx": 0, "prompt_tokens": 8, "completion_tokens": 4, "ok": True,
                      "chunk_epochs": [10.0, 20.0, 30.0, 40.0]}],
    })
    (source.parent / "meta.env").write_text(
        "INPUT_LEN=8\nPREFIX_LEN=0\nOUTPUT_LEN=4\nCONCURRENCY=1\nSPEC_K=0\nNUM_LAYERS=2\nTP=4\nDP=1\nEP=4\nNPU_TYPE=Ascend950PR_A5\n",
        encoding="utf-8",
    )
    _write(source.parent / "run_meta.json", {
        "npu_type": "Ascend950PR_A5", "host": "177.31.22.1", "timestamp_utc": "2026-10-31T19:22:11Z",
        "workload": {"input_len": 8, "output_len": 4, "prefix_len": 0},
    })
    (source.parent / "cmd.sh").write_text(
        "vllm serve model --tensor-parallel-size 4 --data-parallel-size 1 "
        "--compilation-config '{\"cudagraph_mode\":\"FULL_DECODE_ONLY\",\"cudagraph_capture_sizes\":[1,2,4]}'\n",
        encoding="utf-8",
    )
    receipt = tmp_path / "extractions" / ("a" * 64 + ".json")
    document = json.loads(receipt.read_text(encoding="utf-8"))
    document["observed"]["forwards"] = [
        {"forward_id": "auto:0", "phase": "decode", "rank_id": "", "device_id": "0", "query_rows": 1},
        {"forward_id": "auto:1", "phase": "decode", "rank_id": "", "device_id": "0", "query_rows": 1},
    ]
    document["observed"]["source_identity"]["sha256"] = _sha(source)
    document["observed"]["source_identity"]["size_bytes"] = source.stat().st_size
    receipt.write_text(json.dumps(document), encoding="utf-8")
    archive.clear_archive_caches()
    row = _row(source)
    result = archive.resolve_archive_case(row)
    frames = result["geometry"]["frames"]
    assert result["status"] == "resolved", result["diagnostics"]
    assert [(item["forward_id"], item["context_tokens"], item["receipt_forward_id"], item["graph_capture_bucket"]) for item in frames] == [
        (2, 9, "auto:0", 1), (3, 10, "auto:1", 1),
    ]
    assert frames[0]["rank_id"] is None and frames[0]["receipt_rank_id"] == ""
    assert frames[0]["graph_capture_mode"] == "FULL_DECODE_ONLY"
    assert result["case"]["runtime"]["graph_capture_keys"] == [1, 2, 4]
    assert frames[0]["graph_bucket_bounds_query_not_context"] is True
    assert result["geometry"]["executed_graph"]["context_tokens_min"] == 9
    assert result["geometry"]["executed_graph"]["context_tokens_max"] == 10
    assert result["geometry"]["executed_graph"]["selected"] is False
    assert result["geometry"]["window_fields"]["per_window_dp"] is False
    assert result["geometry"]["window_fields"]["deployment_dp"] == 1
    assert "per_window_dp_absent" in result["diagnostics"]
    assert result["case"]["machine"]["sku"] == "Ascend950PR_9579"
    scenarios = result["geometry"]["conditional_scenarios"]
    assert [item["catalog_sku"] for item in scenarios] == ["Ascend950PR_9579", "Ascend910B4"]
    assert scenarios[0]["parseable"] is True and scenarios[0]["applied"] is True
    assert scenarios[0]["exact"] is False and scenarios[0]["selected"] is False
    assert scenarios[0]["case"]["machine"]["sku"] == "Ascend950PR_9579"
    assert scenarios[1]["parseable"] is False and scenarios[1]["applied"] is False and "case" not in scenarios[1]
    assert scenarios[1]["reason"] == "contrary_template"
    assert result["geometry"]["device_inventory"]["host"] == "177.31.22.1"
    assert result["geometry"]["device_inventory"]["physical_serial"] is None
    assert result["geometry"]["device_inventory"]["device_info_retained"] is False
    assert result["geometry"]["device_inventory"]["label_role"] == "producer_deployment_setting"
    assert result["geometry"]["device_inventory"]["measured_from_npu_smi"] is False
    poisoned = dict(row)
    poisoned.update(observed_ms=1, predicted_ms=2, kernel_summary={"poison": True}, structural_weights=[1])
    archive.clear_archive_caches()
    again = archive.resolve_archive_case(poisoned)
    assert again["geometry"]["frames"] == result["geometry"]["frames"]
    assert again["diagnostics"] == result["diagnostics"]


def test_declared_pr_a5_beats_the_dt_template_without_becoming_exact(tmp_path):
    source = _layout(tmp_path)
    case_path = tmp_path / "cases" / "a2-dsv2lite-w8a8-tp4ep4.json"
    document = json.loads(case_path.read_text(encoding="utf-8"))
    document["machine"]["sku"] = "Ascend950DT_9582"
    case_path.write_text(json.dumps(document), encoding="utf-8")
    (source.parent / "meta.env").write_text("NPU_TYPE=Ascend950PR_A5\nHOST=177.31.22.1\n", encoding="utf-8")
    _write(source.parent / "run_meta.json", {"npu_type": "Ascend950PR_A5", "host": "177.31.22.1"})
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source, hardware_tier="A5"))
    assert result["status"] == "resolved", result["diagnostics"]
    assert result["case"]["machine"]["sku"] == "Ascend950PR_9579"
    assert "hardware_sku_declared_not_serial_verified" in result["diagnostics"]
    rows = result["geometry"]["hardware_candidates"]
    assert rows[0]["applied"] is True and rows[0]["exact"] is False and rows[0]["equipment_proof"] is None
    assert rows[1]["declared_identity"] == "Ascend950DT_9582" and rows[1]["applied"] is False
    assert rows[1]["role"] == "contrary_template"
    assert rows[1]["source"] == "template_machine.sku+eval_a5_wave5.HW_A5"
    assert result["geometry"]["conditional_scenarios"][1]["parseable"] is False
    _write(source.parent / "run_meta.json", {"npu_type": "Ascend950DT_9582", "host": "177.31.22.1"})
    archive.clear_archive_caches()
    split = archive.resolve_archive_case(_row(source, hardware_tier="A5"))
    assert "sku" not in split["case"]["machine"]
    assert "hardware_sku_conditional_not_exact" in split["diagnostics"]
    assert all(item["applied"] is False for item in split["geometry"]["hardware_candidates"])


def test_unmapped_a2_declaration_does_not_inherit_template_b4(tmp_path):
    source = _layout(tmp_path)
    (source.parent / "meta.env").write_text("NPU_TYPE=Ascend910B_A2\nHOST=173.125.1.2\n", encoding="utf-8")
    _write(source.parent / "run_meta.json", {"npu_type": "Ascend910B_A2", "host": "173.125.1.2"})
    archive.clear_archive_caches()
    result = archive.resolve_archive_case(_row(source))
    assert result["status"] == "resolved", result["diagnostics"]
    assert "sku" not in result["case"]["machine"]
    assert "hardware_sku_conditional_not_exact" in result["diagnostics"]
    assert "hardware_sku_declared_not_serial_verified" not in result["diagnostics"]
    declared, template = result["geometry"]["hardware_candidates"]
    assert declared["declared_identity"] == "Ascend910B_A2" and declared["catalog_sku"] is None
    assert declared["role"] == "producer_deployment_setting" and declared["applied"] is False
    assert template["catalog_sku"] == "Ascend910B4" and template["applied"] is False
    assert template["role"] == "template_subtype_not_measurement"
    scenarios = result["geometry"]["conditional_scenarios"]
    assert all(item["parseable"] is False and "case" not in item for item in scenarios)
    assert scenarios[0]["reason"] == "declared_identity_has_no_catalog_sku"
    assert result["geometry"]["device_inventory"]["measured_from_npu_smi"] is False
    assert result["geometry"]["device_inventory"]["label_role"] == "producer_deployment_setting"
