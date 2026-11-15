"""Focused tests for source-declared A5 campaign case materialization."""
from __future__ import annotations

import csv
import gzip
import json
import sys
from pathlib import Path

import pytest

STRUCT = Path(__file__).resolve().parents[1] / "examples" / "structure"
SIM = Path(__file__).resolve().parents[2] / "sim"
for item in (str(STRUCT), str(SIM)):
    if item not in sys.path:
        sys.path.insert(0, item)

import fleet_campaign_case as fc
import fleet_campaign_geometry as fc_geom
import fleet_campaign_observation_boundary as obs_boundary


_MODEL = {
    "model_type": "moe",
    "architectures": ["MoeForCausalLM"],
    "hidden_size": 64,
    "num_hidden_layers": 2,
    "num_attention_heads": 4,
    "num_key_value_heads": 4,
    "intermediate_size": 128,
    "moe_intermediate_size": 64,
    "n_routed_experts": 8,
    "num_experts_per_tok": 2,
    "vocab_size": 128,
    "max_position_embeddings": 8192,
}


def _write(path: Path, value) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _model_catalog(root: Path, quant: str | None = None) -> Path:
    directory = root / "ModelA"
    _write(directory / "config.json", _MODEL)
    if quant:
        _write(directory / "quant_model_description.json", {
            "metadata": {},
            "model.layers.0.mlp.down_proj.weight": quant,
            "model.layers.0.mlp.down_proj.weight_scale": quant,
            "model.layers.1.mlp.down_proj.weight": quant,
            "model.layers.1.self_attn.q_proj.weight": "FLOAT",
        })
    return directory


def _preflight(workstream: Path) -> None:
    rows = []
    for node in ("10.0.0.1", "10.0.0.2"):
        lines = ["| NPU ID | Name | Health | Power(W) | Temp(C) Hugepages |"]
        for index in range(8):
            lines.append(f"| {index} | Ascend950DT | OK | 1 | 1 / 0 |")
            lines.append("|   |   | NA | 2 | 4782 / 98304 |")
        rows.append({"node": node, "hostname": f"host-{node}", "npu_raw": "\n".join(lines)})
    _write(workstream / "a5-multinode-fleet-rack06-20261107" / "evidence" / "preflight_case.json", rows)


def _campaign(root: Path, *, mode: str = "decode_steady") -> Path:
    run = root / "runs" / "caseA"
    _write(run / "case_spec.json", {
        "case_id": "caseA", "model_path": "/mnt/weight/ModelA", "tp": 2, "dp": 4,
        "enable_expert_parallel": True, "max_num_seqs": 8, "max_num_batched_tokens": 4096,
        "max_model_len": 8192, "cells": [{"tag": "cellA", "mode": mode, "isl": 2048,
                                          "osl": 32, "concurrency": 4}],
    })
    _write(run / "manifest.json", {"case_id": "caseA", "model_path": "/mnt/weight/ModelA",
                                   "tp": 2, "dp": 4, "nodes": ["10.0.0.1", "10.0.0.2"]})
    _write(run / "cellA.json", {"tag": "cellA", "mode": mode, "isl": 2048, "osl": 32,
                                "concurrency": 4, "prefix_cache_ratio": 0.0})
    return run


def _campaign_row(**overrides) -> dict:
    row = {"capture_id": "a5_multinode_20261108:caseA:cellA", "suite": fc.CAMPAIGN_SUITE,
           "phase": "decode", "geometry": {"tp": 2, "dp": 4, "ep": 8, "concurrency": 4}}
    row.update(overrides)
    return row


def _rack(workstream: Path) -> Path:
    base = workstream / "a5-multinode-fleet-rack06-20261107"
    _write(base / "cases" / "caseR.json", {
        "id": "caseR", "model": "/mnt/weight/ModelA", "tp": 1, "dp": 2,
        "enable_expert_parallel": True, "max_num_seqs": 4, "max_num_batched_tokens": 2048,
        "max_model_len": 8192, "nodes": ["10.0.0.1", "10.0.0.2"],
    })
    cell = base / "out" / "caseR" / "dc_1k_c2"
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "cmd.sh").write_text(
        "python bench_cell.py --mode profile_decode --prompt-tokens 1024 "
        "--max-tokens 16 --concurrency 2 --shared-tokens 512 --tag x\n",
        encoding="utf-8")
    (cell / "10.0.0.1" / "dp1_pp0_tp0_dcp0_ep1_rank0_1_ascend_pt").mkdir(parents=True)
    return base


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path):
    fc.configure_sources(campaign_root=tmp_path / "campaign", weights_catalog=tmp_path / "weights",
                         workstream_roots=(tmp_path / "workstreams",))
    _model_catalog(tmp_path / "weights")
    _preflight(tmp_path / "workstreams")
    yield
    fc.clear_caches()


def test_campaign_uses_declared_parallel_and_phase(tmp_path: Path):
    _campaign(tmp_path / "campaign")
    result = fc.resolve_campaign_case(_campaign_row())
    assert result is not None and result["ok"], result
    assert result["parallel"] == {"tp": 2, "dp": 4, "ep": 8, "pp": 1}
    assert result["geometry"]["phase"] == "decode"
    assert result["sequences"] == 1 and result["tokens"] == 1 and result["context"] == 2048
    assert result["workload"]["prompt_tokens"] == 2048
    assert result["sku"] == "Ascend950DT_9582"
    assert Path(result["source"]["case_spec"]["path"]).name == "case_spec.json"
    assert Path(result["source"]["cell_launch"]["path"]).name == "cellA.json"
    assert result["case"]["runtime"]["parallel"]["ep"] == 8


def test_campaign_prefill_declares_prompt_and_zero_context(tmp_path: Path):
    _campaign(tmp_path / "campaign", mode="prefill_only")
    result = fc.resolve_campaign_case(_campaign_row(phase="prefill"))
    assert result["ok"], result
    assert result["geometry"]["phase"] == "prefill"
    assert result["tokens"] == 2048 and result["context"] == 0
    assert result["workload"]["output_tokens"] == 32
    assert result["runtime"]["max_num_batched_tokens"] == 4096
    assert result["runtime"]["enable_chunked_prefill"] is True


def test_replica_batch_is_declared_concurrency_over_dp(tmp_path: Path):
    run = _campaign(tmp_path / "campaign")
    for name in ("case_spec.json", "manifest.json"):
        payload = json.loads((run / name).read_text(encoding="utf-8"))
        payload["dp"] = 8
        payload["tp"] = 1
        _write(run / name, payload)
    cell = json.loads((run / "cellA.json").read_text(encoding="utf-8"))
    cell["concurrency"] = 64
    _write(run / "cellA.json", cell)
    result = fc.resolve_campaign_case(_campaign_row(geometry={}))
    assert result["ok"], result
    assert result["parallel"]["dp"] == 8
    assert result["geometry"]["sequences_per_replica"] == 8
    assert result["geometry"]["query_rows"] == 8
    assert result["geometry"]["concurrency"] == 64


def test_rack_launcher_supplies_exact_rank_population(tmp_path: Path):
    _rack(tmp_path / "workstreams")
    row = {"capture_id": ("a5_rack06_rack08_multirank_20261107:a5-multinode-fleet-rack06-20261107/"
                          "out/caseR/dc_1k_c2/10.0.0.1/dp1_pp0_tp0_dcp0_ep1_rank0_1_ascend_pt"),
           "suite": fc.RACK_SUITE, "phase": "decode"}
    result = fc.resolve_campaign_case(row)
    assert result is not None and result["ok"], result
    assert result["parallel"] == {"tp": 1, "dp": 2, "ep": 2, "pp": 1}
    assert result["sequences"] == 1 and result["context"] == 1024
    assert result["workload"] == {"prompt_tokens": 1024, "output_tokens": 16,
                                  "prefix_tokens": 512, "concurrency": 2}
    assert Path(result["source"]["cell_launcher"]["path"]).name == "cmd.sh"


def test_measurement_and_target_fields_do_not_change_resolution(tmp_path: Path):
    _campaign(tmp_path / "campaign")
    base = fc.resolve_campaign_case(_campaign_row())
    poisoned = _campaign_row(observed_ms=999.0, tpot_ms=1.0, kernel_summary={"total_kernel_duration_us": 1},
                             structural_weights={"x": 1}, active_hbm_mb=1, active_cube_gflops=1,
                             target_timing_used_to_fit=True)
    other = fc.resolve_campaign_case(poisoned)
    assert base["case"] == other["case"]
    assert base["geometry"] == other["geometry"]
    assert base["source"] == other["source"]


def test_missing_source_fails_closed_and_keeps_identity(tmp_path: Path):
    _campaign(tmp_path / "campaign")
    row = _campaign_row(capture_id="a5_multinode_20261108:missing_case:cellA")
    result = fc.resolve_campaign_case(row)
    assert result is not None and not result["ok"]
    assert "campaign_case_spec_or_manifest_missing" in result["diagnostics"]


def test_mixed_window_models_declared_decode_population(tmp_path: Path):
    _campaign(tmp_path / "campaign", mode="mixed_multiturn")
    result = fc.resolve_campaign_case(_campaign_row())
    assert result["ok"], result
    assert result["geometry"]["population_basis"] == "mixed_multiturn_decode_tpot"
    assert "mixed_window_decode_population:profile_window_contains_prefill_and_decode" in result["diagnostics"]


def test_parallel_conflict_is_reported_and_declaration_wins(tmp_path: Path):
    _campaign(tmp_path / "campaign")
    result = fc.resolve_campaign_case(_campaign_row(geometry={"tp": 2, "dp": 8, "ep": 16}))
    assert result["ok"]
    assert result["parallel"] == {"tp": 2, "dp": 4, "ep": 8, "pp": 1}
    assert any(item.startswith("row_dp_8_disagrees_with_declaration_4") for item in result["diagnostics"])


def test_out_of_scope_row_returns_none():
    assert fc.resolve_campaign_case({"capture_id": "registered_decode:x", "suite": "registered_decode"}) is None


def test_quant_description_uses_dominant_declared_weight_class(tmp_path: Path):
    directory = _model_catalog(tmp_path / "weights")
    _write(directory / "quant_model_description.json", {
        "metadata": {},
        **{f"model.layers.0.mlp.{index}.weight": "W4A4_MXFP4" for index in range(20)},
        "model.layers.0.self_attn.q_proj.weight": "W8A8_MXFP8",
    })
    fc.clear_caches()
    model = fc._model_config("/mnt/weight/ModelA")
    assert model["quant"] == "mxfp4"
    assert model["quant_source"]["dominant_weight_tensors"] == 20


def test_idle_rank_export_is_modeled_with_basis(tmp_path: Path):
    _campaign(tmp_path / "campaign")
    result = fc.resolve_campaign_case(_campaign_row())
    idle = fc.resolve_campaign_case(_campaign_row(
        capture_id="a5_multinode_20261108:caseA:cellA:idle_dp_rank"))
    assert idle["ok"], idle
    assert idle["geometry"]["rank_export"] == "idle_dp_rank"
    assert idle["geometry"]["rank_batch_observed"] is False
    assert "rank_export_label:idle_dp_rank" in idle["diagnostics"]
    assert idle["case"] == result["case"]
    assert idle["deployment_sha256"] == result["deployment_sha256"]


def test_declared_graph_mode_and_speculative_tokens_materialize(tmp_path: Path):
    run = _campaign(tmp_path / "campaign")
    spec = json.loads((run / "case_spec.json").read_text(encoding="utf-8"))
    spec["compilation_config"] = {"cudagraph_mode": "FULL_DECODE_ONLY",
                                  "cudagraph_capture_sizes": [1, 2, 4, 8, 16]}
    spec["speculative_config"] = {"method": "qwen3_5_mtp", "num_speculative_tokens": 3}
    _write(run / "case_spec.json", spec)
    result = fc.resolve_campaign_case(_campaign_row())
    assert result["ok"], result
    assert result["graph_mode"] == "full"
    assert result["mtp_proposal_tokens"] == 3
    assert result["case"]["runtime"]["graph_capture_keys"] == [1, 2, 4, 8, 16]
    assert result["case"]["runtime"]["metadata"]["draft_proposal_tokens"] == 3
    assert result["tokens"] == 4
    assert result["geometry"]["tokens_basis"] == "declared_speculative_policy_bound"
    assert result["geometry"]["actual_q_observed"] is False
    assert result["deployment_sha256"]


def test_additional_config_and_scheduler_features_reach_runtime(tmp_path: Path):
    run = _campaign(tmp_path / "campaign")
    glm = tmp_path / "weights" / "GLM-5.1-w4a4c8-mxfp4"
    _write(glm / "config.json", _MODEL)
    spec = json.loads((run / "case_spec.json").read_text(encoding="utf-8"))
    spec["model_path"] = "/mnt/weight/GLM-5.1-w4a4c8-mxfp4"
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    manifest["model_path"] = "/mnt/weight/GLM-5.1-w4a4c8-mxfp4"
    _write(run / "manifest.json", manifest)
    spec["additional_config"] = {
        "enable_shared_expert_dp": True,
        "multistream_overlap_shared_expert": True,
        "enable_flashcomm1": True,
    }
    spec["gpu_memory_utilization"] = 0.97
    spec["block_size"] = 32
    spec["attention_config"] = {"indexer_kv_dtype": "fp8"}
    spec["enable_prefix_caching"] = False
    _write(run / "case_spec.json", spec)
    cell = json.loads((run / "cellA.json").read_text(encoding="utf-8"))
    cell["prefix_cache_ratio"] = 0.5
    _write(run / "cellA.json", cell)

    first = fc.resolve_campaign_case(_campaign_row())
    assert first["ok"], first
    runtime = first["case"]["runtime"]
    metadata = runtime["metadata"]
    assert metadata["additional_config"] == spec["additional_config"]
    assert metadata["enable_shared_expert_dp"] is True
    assert runtime["multistream_overlap_shared_expert"] is True
    assert runtime["gpu_memory_utilization"] == 0.97
    assert runtime["kv_block_size"] == 32
    assert metadata["attention_config"] == {"indexer_kv_dtype": "fp8"}
    assert metadata["indexer_kv_dtype"] == "fp8_e4m3"
    assert first["case"]["model"]["quant"]["index_dtype"] == "fp8_e4m3"
    assert all(item["prefix_tokens"] == 0 for item in first["case"]["workload"]["requests"])

    # A source-only additional-config change must not inherit the prior deployment id.
    spec["additional_config"] = {"multistream_overlap_shared_expert": True}
    _write(run / "case_spec.json", spec)
    fc.clear_caches()
    second = fc.resolve_campaign_case(_campaign_row())
    assert second["ok"], second
    assert second["deployment_sha256"] != first["deployment_sha256"]


def test_impossible_rank_worker_fails_closed(tmp_path: Path):
    _rack(tmp_path / "workstreams")
    row = {"capture_id": ("a5_rack06_rack08_multirank_20261107:a5-multinode-fleet-rack06-20261107/"
                          "out/caseR/dc_1k_c2/10.0.0.1/dp999_pp0_tp999_dcp0_ep999_rank999_x"),
           "suite": fc.RACK_SUITE, "phase": "decode"}
    result = fc.resolve_campaign_case(row)
    assert not result["ok"]
    assert result["diagnostics"][0].startswith("rank_worker_directory_not_unique")


def test_node_without_own_hardware_facts_fails_closed(tmp_path: Path):
    _campaign(tmp_path / "campaign")
    run = tmp_path / "campaign" / "runs" / "caseA"
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    manifest["nodes"] = ["10.0.0.1", "10.9.9.9"]
    _write(run / "manifest.json", manifest)
    result = fc.resolve_campaign_case(_campaign_row())
    assert not result["ok"]
    assert "hardware_sku_not_declared_for_nodes" in result["diagnostics"]


def test_heterogeneous_quant_classes_are_retained(tmp_path: Path):
    directory = _model_catalog(tmp_path / "weights")
    _write(directory / "quant_model_description.json", {
        "metadata": {},
        **{f"model.layers.0.mlp.{index}.weight": "W4A4_MXFP4" for index in range(20)},
        "model.layers.0.self_attn.q_proj.weight": "W8A8_MXFP8",
    })
    fc.clear_caches()
    model = fc._model_config("/mnt/weight/ModelA")
    assert model["weight_classes"] == {"mxfp4": 20, "mxfp8": 1}
    assert model["quant"] == "mxfp4"


def test_ambiguous_sku_candidates_are_preserved(monkeypatch):
    profile = {"architecture": "A5", "device": {"memory_bytes": 96 * 1024 ** 3}}
    other = {"architecture": "A5", "device": {"memory_bytes": 97 * 1024 ** 3}}
    monkeypatch.setattr(fc, "_sku_profiles", lambda: {"SKU_A": profile, "SKU_B": other})
    monkeypatch.setattr(fc, "_hardware_index", lambda: {"nodes": {
        "n1": {"device_name": "", "hbm_mib": None, "npu_count": 8, "evidence": []}}})
    result = fc._resolve_hardware(["n1"], 93952)
    assert result["sku"] is None
    assert result["candidates"] == ["SKU_A", "SKU_B"]
    monkeypatch.undo()


def test_campaign_export_rank_is_source_metadata(tmp_path: Path):
    run = _campaign(tmp_path / "campaign")
    _write(run / "cellA" / "profiler_info_3.json", {"rank_id": 7, "cann_version": "9.2.0"})
    result = fc.resolve_campaign_case(_campaign_row())
    assert result["ok"], result
    assert result["source"]["export_rank"]["rank_id"] == 7
    assert result["geometry"]["sequences_observed"] is False
    assert result["geometry"]["sequences_upper_bound"] == 1


def test_ambiguous_sku_failure_reports_candidates(tmp_path: Path, monkeypatch):
    _campaign(tmp_path / "campaign")
    monkeypatch.setattr(fc, "_resolve_hardware",
                        lambda *args, **kwargs: {"sku": None, "candidates": ["SKU_A", "SKU_B"],
                                                 "evidence": []})
    result = fc.resolve_campaign_case(_campaign_row())
    assert not result["ok"]
    assert "hardware_sku_ambiguous_catalogue_capacity" in result["diagnostics"]
    assert "candidate:SKU_A" in result["diagnostics"]
    assert result["source"]["hardware_candidates"] == ["SKU_A", "SKU_B"]
    monkeypatch.undo()


def _geometry_export(root: Path, *, shapes=("8", "4"), requests=True, rank=1) -> Path:
    directory = root / "export"
    directory.mkdir(parents=True)
    header = "Device_id,Model ID,Task ID,Stream ID,Name,Type,OP State,Accelerator Core,Start Time(us),Duration(us),Wait Time(us),Block Num,Mix Block Num,HF32 Eligible,Input Shapes,Input Data Types,Input Formats,Output Shapes,Output Data Types,Output Formats,Context ID\n"
    with gzip.open(directory / "kernel_details.csv.gz", "wt", newline="") as stream:
        stream.write(header)
        for shape in shapes:
            stream.write(f'4,1,1,1,FusedInferAttentionScore,attention,static,AI_CORE,1.0,1.0,0,1,0,NO,"{shape},4,256;32280,128,256;32280,128,256",BF16,ND,"{shape},4,256",BF16,ND,N/A\n')
        stream.write('4,1,2,1,aclnnMatmul_MatMulV3,MatMul,static,AI_CORE,1.0,1.0,0,1,0,NO,"8,4096;512,4096",BF16,ND,"8,512",BF16,ND,N/A\n')
    _write(directory / "profiler_info_1.json", {"rank_id": rank, "start_info": {"start_cnt": 1, "start_monotonic": 2}, "end_info": {"collectionTimeEnd": 3}})
    if requests:
        (directory / "request_summary.csv").write_text(
            "tag,mode,req_idx,turn_idx,concurrency,isl,osl_target,ok,status,ttft_ms,tpot_ms,e2e_ms,out_tokens\n"
            "x,decode_steady,0,1,1,1024,64,1,200,0,0,0,24\n"
            "x,decode_steady,1,1,1,1024,64,1,200,0,0,0,21\n", encoding="utf-8")
    (directory / "step_trace_time.csv").write_text(
        "Device_id,Step,Computing,Communication(Not Overlapped),Overlapped,Communication,Free,Stage,Bubble\n"
        "4,,1,0,0,0,0,1,0\n", encoding="utf-8")
    return directory


def test_geometry_probe_binds_rank_and_flags_nonunique_query(tmp_path: Path):
    directory = _geometry_export(tmp_path)
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE}
    binding = fc_geom.probe_rank_binding(row, override=directory)
    geometry = fc_geom.attention_query_candidates(row, override=directory, declared_mtp=3)
    assert binding["profiler_info"]["rank_id"] == 1
    assert binding["kernel"]["device_ids"] == [4]
    assert binding["request_schedule"]["count"] == 2
    assert binding["binding"]["pid_observed"] is False
    assert binding["step_trace"]["forward_ordinal_observed"] is False
    assert geometry["q_candidates"] == {8: 1, 4: 1}
    assert geometry["declared_policy_q"] == 4 and geometry["policy_present"] is True
    assert geometry["unique_query_identified"] is False
    assert "multiple_attention_query_buckets" in geometry["residual"]


def test_geometry_digest_blind_to_ids_targets_and_sensitive_to_exogenous_state(tmp_path: Path):
    directory = _geometry_export(tmp_path)
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE}
    base_b, base_g = fc_geom.probe_rank_binding(row, override=directory), fc_geom.attention_query_candidates(row, override=directory, declared_mtp=3)
    base = fc_geom.canonical_digest(base_b, base_g)
    poisoned = dict(row, case_id="bogus", model_case="bogus", observed_ms=1e9, tpot_ms=1e9,
                    kernel_summary={"total_kernel_duration_us": 1}, structural_weights=[9] * 6,
                    active_hbm_mb=1, active_cube_gflops=1)
    poisoned_b = fc_geom.probe_rank_binding(poisoned, override=directory)
    poisoned_g = fc_geom.attention_query_candidates(poisoned, override=directory, declared_mtp=3)
    assert fc_geom.canonical_digest(poisoned_b, poisoned_g) == base
    changed_g = fc_geom.attention_query_candidates(row, override=directory, declared_mtp=1)
    assert fc_geom.canonical_digest(base_b, changed_g) != base


def test_geometry_na_shapes_are_not_treated_as_unique(tmp_path: Path):
    directory = _geometry_export(tmp_path, shapes=())
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE}
    geometry = fc_geom.attention_query_candidates(row, override=directory, declared_mtp=0)
    assert geometry["attention_rows"] == 0
    assert geometry["shape_rows"] == 0
    assert geometry["unique_query_identified"] is False
    assert "attention_shapes_na_or_absent" in geometry["residual"]


def test_geometry_single_real_shape_can_be_unique(tmp_path: Path):
    directory = _geometry_export(tmp_path, shapes=("1",))
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE}
    geometry = fc_geom.attention_query_candidates(row, override=directory, declared_mtp=0)
    assert geometry["shape_rows"] == 1
    assert geometry["q_candidates"] == {1: 1}
    assert geometry["unique_query_identified"] is True


def test_geometry_narrow_decode_candidate_is_not_actual(tmp_path: Path):
    directory = _geometry_export(tmp_path, shapes=("1", "896"))
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE}
    geometry = fc_geom.attention_query_candidates(row, override=directory, declared_mtp=0,
                                                  max_num_seqs=128)
    assert geometry["decode_q_candidates"] == {1: 1}
    assert geometry["single_decode_bucket_candidate"] is True
    assert geometry["actual_query_identified"] is False


def test_geometry_launch_pids_are_source_evidence(tmp_path: Path):
    directory = _geometry_export(tmp_path)
    (directory / "kv_cache_startup.json").write_text(json.dumps({"matched_startup_lines": [
        "(Worker_TP0 pid=472) INFO 11-08 09:17:50 model loading",
        "(Worker_TP1 pid=543) INFO 11-08 09:17:50 model loading",
        "(EngineCore_DP0 pid=317) INFO boot"]}), encoding="utf-8")
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE}
    binding = fc_geom.probe_rank_binding(row, override=directory)
    assert binding["launch_processes"]["pid_observed"] is True
    assert {"role": "Worker", "pid": 472} in binding["launch_processes"]["processes"]
    assert binding["binding"]["pid_observed"] is True
    assert binding["binding"]["host_observed"] is False


def test_forward_ordinal_markers_group_attention_shapes(tmp_path: Path):
    directory = tmp_path / "export"
    directory.mkdir()
    header = "Device_id,Model ID,Task ID,Stream ID,Name,Type,OP State,Accelerator Core,Start Time(us),Duration(us),Wait Time(us),Block Num,Mix Block Num,HF32 Eligible,Input Shapes,Input Data Types,Input Formats,Output Shapes,Output Data Types,Output Formats,Context ID\n"
    def row(name, start, shapes):
        return f'4,1,1,1,{name},x,static,AI_CORE,{start},1,0,1,0,NO,"{shapes}",BF16,ND,"1",BF16,ND,N/A\n'
    with gzip.open(directory / "kernel_details.csv.gz", "wt", newline="") as stream:
        stream.write(header)
        stream.write(row("_combine_sampled_and_draft_tokens_kernel", "1", "1;64,1;3;2"))
        stream.write(row("FusedInferAttentionScore", "2", "8,4,256;32280,128,256;32280,128,256"))
        stream.write(row("_combine_sampled_and_draft_tokens_kernel", "10", "1;64,1;3;2"))
        stream.write(row("FusedInferAttentionScore", "11", "4,4,256;32280,128,256;32280,128,256"))
    result = fc_geom.forward_ordinal_candidates(
        {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE},
        override=directory, max_num_seqs=128)
    assert result["marker_counts"]["combine"] == 2
    assert result["by_marker"]["combine"]["intervals_with_shapes"] == 2
    assert result["by_marker"]["combine"]["q_by_ordinal"][0]["q_counts"] == {8: 1}
    assert result["by_marker"]["combine"]["q_by_ordinal"][1]["q_counts"] == {4: 1}
    assert result["actual_batch_identified"] is False


def test_forward_ordinal_can_identify_retained_rank_decode_query(tmp_path: Path):
    directory = tmp_path / "export"
    directory.mkdir()
    header = "Device_id,Model ID,Task ID,Stream ID,Name,Type,OP State,Accelerator Core,Start Time(us),Duration(us),Wait Time(us),Block Num,Mix Block Num,HF32 Eligible,Input Shapes,Input Data Types,Input Formats,Output Shapes,Output Data Types,Output Formats,Context ID\n"
    def row(name, start, shapes):
        return f'4,1,1,1,{name},x,static,AI_CORE,{start},1,0,1,0,NO,"{shapes}",BF16,ND,"1",BF16,ND,N/A\n'
    with gzip.open(directory / "kernel_details.csv.gz", "wt", newline="") as stream:
        stream.write(header)
        stream.write(row("_combine_sampled_and_draft_tokens_kernel", "1", "1;64,1;3;2"))
        stream.write(row("FusedInferAttentionScore", "2", "896,4,256;32280,128,256;32280,128,256"))
        stream.write(row("_combine_sampled_and_draft_tokens_kernel", "10", "1;64,1;3;2"))
        stream.write(row("FusedInferAttentionScore", "11", "1,4,256;32280,128,256;32280,128,256"))
    result = fc_geom.forward_ordinal_candidates(
        {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE},
        override=directory, max_num_seqs=128)
    combine = result["by_marker"]["combine"]
    assert combine["decode_q_values"] == [1]
    assert combine["prefill_ordinals"] == [0]
    assert combine["retained_rank_decode_query_identified"] is True
    assert result["actual_batch_identified"] is True
    assert result["active_rank_identified"] is False


def test_sibling_rank_device_conflict_is_exposed(tmp_path: Path):
    primary = tmp_path / "primary"
    primary.mkdir()
    _write(primary / "profiler_info_1.json", {"rank_id": 1})
    import gzip
    with gzip.open(primary / "kernel_details.csv.gz", "wt", newline="") as stream:
        stream.write("Device_id,Name,Input Shapes\n")
        stream.write("5,FusedInferAttentionScore,\"1,1,1\"\n")
    idle = primary / "idle_dp_rank"
    idle.mkdir()
    _write(idle / "profiler_info_1.json", {"rank_id": 1})
    with gzip.open(idle / "kernel_details.csv.gz", "wt", newline="") as stream:
        stream.write("Device_id,Name,Input Shapes\n")
        stream.write("1,FusedInferAttentionScore,\"1,1,1\"\n")
    result = fc_geom._sibling_identity(idle, {"kind": "campaign"})
    assert result["has_sibling"] is True
    assert result["same_rank"] is True
    assert result["same_device"] is False
    assert result["same_rank_different_device"] is True


def test_engine_schedule_is_source_evidence(tmp_path: Path):
    directory = _geometry_export(tmp_path)
    (tmp_path / "vllm_rank0.log").write_text(
        "Engine 000: Avg prompt throughput: 1 tokens/s, Running: 0 reqs, Waiting: 0 reqs\n"
        "Engine 001: Avg prompt throughput: 2 tokens/s, Running: 1 reqs, Waiting: 0 reqs\n",
        encoding="utf-8")
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE}
    binding = fc_geom.probe_rank_binding(row, override=directory)
    schedule = binding["engine_schedule"]
    assert schedule["engine_schedule_observed"] is True
    assert schedule["engine_ids"] == [0, 1]
    assert schedule["active_engines"] == [1]
    assert binding["binding"]["engine_schedule_observed"] is True


def _boundary_export(root: Path, *, marker_starts=("1", "10"), declared=2, request=True):
    directory = _geometry_export(root, shapes=("1",), requests=request)
    header = "Device_id,Model ID,Task ID,Stream ID,Name,Type,OP State,Accelerator Core,Start Time(us),Duration(us),Wait Time(us),Block Num,Mix Block Num,HF32 Eligible,Input Shapes,Input Data Types,Input Formats,Output Shapes,Output Data Types,Output Formats,Context ID\n"
    with gzip.open(directory / "kernel_details.csv.gz", "wt", newline="") as stream:
        stream.write(header)
        for index, start in enumerate(marker_starts):
            stream.write(f'4,1,1,1,_combine_sampled_and_draft_tokens_kernel,x,static,AI_CORE,{start},1,0,1,0,NO,"1;64,1;3;2",INT64,ND,"1",INT64,ND,N/A\n')
            stream.write(f'4,1,1,1,FusedInferAttentionScore,x,static,AI_CORE,{float(start)+0.5},1,0,1,0,NO,"1,4,256;32280,128,256;32280,128,256",BF16,ND,"1",BF16,ND,N/A\n')
    return directory


def test_boundary_marks_marker_interval_candidate(tmp_path: Path):
    directory = _boundary_export(tmp_path, declared=2)
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE,
           "forward_steps": 2}
    result = obs_boundary.reconstruct_observation_boundary(
        row, override=directory, max_num_seqs=128)
    assert result["status"] == "marker_interval_candidate"
    assert result["source_unit"] == "per_forward_marker_interval"
    assert result["marker_consistency"]["marker_count"] == 2
    assert result["intervals"][0]["q_counts"] == {1: 1}


def test_boundary_rejects_marker_count_mismatch(tmp_path: Path):
    directory = _boundary_export(tmp_path, declared=64)
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE,
           "forward_steps": 64}
    result = obs_boundary.reconstruct_observation_boundary(
        row, override=directory, max_num_seqs=128)
    assert result["status"] == "no_forward_boundary"
    assert result["marker_consistency"]["reason"] == "marker_count_not_declared_steps"


def test_boundary_uses_request_or_kernel_unit_when_no_marker(tmp_path: Path):
    directory = _geometry_export(tmp_path, shapes=("1",), requests=False)
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE,
           "forward_steps": 1}
    result = obs_boundary.reconstruct_observation_boundary(
        row, override=directory, max_num_seqs=128)
    assert result["status"] == "no_forward_boundary"
    assert result["source_unit"] == "per_rank_kernel_aggregate"


def test_boundary_uses_operator_aggregate_when_no_kernel(tmp_path: Path):
    directory = _geometry_export(tmp_path, shapes=(), requests=False)
    (directory / "kernel_details.csv.gz").unlink()
    (directory / "op_statistic.csv").write_text(
        "Device_id,OP Type,Core Type,Count\n4,MatMul,AI_CORE,1\n", encoding="utf-8")
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE,
           "forward_steps": 1}
    result = obs_boundary.reconstruct_observation_boundary(row, override=directory, max_num_seqs=128)
    assert result["status"] == "no_forward_boundary"
    assert result["source_unit"] == "operator_aggregate"


def test_boundary_rejects_really_blank_marker_interval(tmp_path: Path):
    directory = _boundary_export(tmp_path, marker_starts=("1", "10", "20"), declared=3)
    row = {"capture_id": "a5_multinode_20261108:case:cell", "suite": fc.CAMPAIGN_SUITE,
           "forward_steps": 3}
    # Remove attention rows wholly inside the middle marker bin, keep all three markers.
    with gzip.open(directory / "kernel_details.csv.gz", "rt") as stream:
        rows = list(csv.DictReader(stream))
    kept = [r for r in rows if not (r["Name"] == "FusedInferAttentionScore"
                                    and 10.0 <= float(r["Start Time(us)"]) < 20.0)]
    with gzip.open(directory / "kernel_details.csv.gz", "wt", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(kept)
    result = obs_boundary.reconstruct_observation_boundary(
        row, override=directory, max_num_seqs=128)
    assert result["status"] == "no_forward_boundary"
    assert result["marker_consistency"]["reason"] == "blank_marker_interval"


def test_boundary_rejects_forged_campaign_suffix(tmp_path: Path):
    directory = _boundary_export(tmp_path, declared=2)
    row = {"capture_id": "a5_multinode_20261108:case:cell:unowned_export",
           "suite": fc.CAMPAIGN_SUITE, "forward_steps": 2}
    result = obs_boundary.reconstruct_observation_boundary(
        row, override=directory, max_num_seqs=128)
    assert result["status"] == "invalid_id"
    assert result["id_status"] == "not_an_original_export_id"


def test_boundary_accepts_legal_idle_suffix_and_reports_spans(tmp_path: Path):
    directory = _boundary_export(tmp_path / "idle", declared=2)
    row = {"capture_id": "a5_multinode_20261108:case:cell:idle_dp_rank",
           "suite": fc.CAMPAIGN_SUITE, "forward_steps": 2}
    result = obs_boundary.reconstruct_observation_boundary(
        row, override=directory, max_num_seqs=128)
    assert result["status"] == "marker_interval_candidate"
    assert result["id_status"] == "original_export_id"
    assert result["marker_consistency"]["complete_span_count"] == 1
    assert result["marker_consistency"]["tail_span_count"] == 1
