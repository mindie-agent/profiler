"""ABI, padding, diff-trace and R1..R6 adversarial coverage.

[Role]
  Exercise the supported end-to-end paths (exact versioned lookup, complete FA
  and GMM slot binding, metadata-exact reproducer generation, diff-trace
  host/comm scenarios, fabric planning/fitting, CLI wiring) plus the R1..R6
  review counterexamples for interval replay, exact lookup, headers, slot
  conservation, descriptor states and layout-qualified padding.

[Invariants]
  * C signatures are grounded by the header parser in the adversarial suite;
    this file covers the public behavior and generated artifacts.
  * No NPU access; generated scripts are only executed with ``--dry-run``.
  * Temporary files stay under ``tmp_path``.

[Timeouts & Locks]
  Pure in-memory work plus bounded generated dry-runs.

[Side-Effect Policy]
  No writes outside ``tmp_path``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from mindie_profiler import repro_atomic_io as checked_io
import re
import subprocess
import sys

import pytest

from mindie_profiler.__main__ import main as profiler_main
from mindie_profiler.fabric_probe import (
    build_fabric_probe_plan, emit_fabric_probe_script, validate_plan,
)
from mindie_profiler.fabric_probe_fit import fit_calibrated_fabric_profile
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.op_abi_binding import slot_descriptors
from mindie_profiler.op_abi_descriptors import parse_shape
from mindie_profiler.op_abi_padding import (
    compute_padding, synthesize_group_list, synthesize_offsets, validate_group_list,
)
from mindie_profiler.op_api_registry import (
    bind_captured_occurrence, catalog_entry, catalog_operator, catalog_summary,
    inspect_op_abi, operator_names,
)
from mindie_profiler.repro_op import _compact_occurrence, generate_single_op_reproducer
from mindie_sim.diff_trace import (
    attribute_diff, effective_operator_rows, pad_aware_operator_cost,
)
from nr_s6_support import _parse_header_signature, fa_row, paged_row

from nr_s6_support import fa_binding, gmm_binding, paged_binding

def test_catalog_schema_and_counts():
    summary = catalog_summary()
    assert summary["schema"] == "mindie-op-api-catalog/2"
    assert summary["operator_count"] == 32
    assert summary["pinned_signatures"] >= 20
    assert set(summary["padding_modes"]) == {
        "masked_varlen", "grouped_prefix", "full_padded_tensor"}
    assert len(operator_names()) == 32

def test_exact_versioned_lookup_and_alias():
    match = catalog_operator("aclnnGroupedMatmulV4", cann_version="9.0")
    assert match and match["name"] == "aclnnGroupedMatmulV4"
    assert match["version_supported"] and match["signature_supported"]
    assert catalog_operator("npu_grouped_matmul", cann_version="9.0")["match"] == "alias"
    assert catalog_operator("aclnnGroupedMatmulV4",
                            cann_version=None)["version_supported"] is False


def test_fa_v1_binding_is_complete_and_conserved():
    binding = fa_binding()
    assert binding["status"] == "bound"
    assert binding["identity"]["catalog_abi_id"].startswith("sha256:")
    assert binding["identity"]["native_abi_sha256"].startswith("sha256:")
    assert binding["conservation"]["exact"] is True
    assert binding["padding"]["bucket_tokens"] == 48
    assert binding["padding"]["effective_tokens"] == 33
    assert binding["padding"]["charged_tokens"] == 33
    assert binding["padding"]["padded_tokens"] == 15


def test_gmm_tensor_list_binding_and_nz_storage():
    binding = gmm_binding()
    assert binding["status"] == "bound"
    assert binding["inputs"][0]["state"] == "tensor_list"
    assert binding["inputs"][0]["items"][0]["layout"] == "ND"
    assert binding["inputs"][1]["items"][0]["layout"] == "FRACTAL_NZ"
    assert binding["padding"]["bucket_tokens"] == 64
    assert binding["padding"]["effective_tokens"] == 64
    assert binding["padding"]["group_mode"] == "cumsum"


def test_paged_attention_binding_and_metadata():
    binding = paged_binding()
    assert binding["status"] == "bound"
    assert binding["padding"]["qualification"]["pa"] is True
    result = generate_single_op_reproducer(binding)
    metadata = result["metadata"]
    assert metadata["install"]
    context = next(item for item in metadata["install"]
                   if item["tensor"] == "context_lens")
    assert context["shape"] == [16] and len(context["values"]) == 16
    table = next(item for item in metadata["install"]
                 if item["tensor"] == "block_table")
    assert table["shape"] == [16, 16]
    assert result["checks"]["block_table_in_bounds"] is True


def test_reproducer_dry_run_and_manifest(tmp_path):
    result = generate_single_op_reproducer(gmm_binding(), output_dir=tmp_path)
    assert result["status"] == "ready"
    assert result["fidelity"] in {"descriptor_synthetic", "value_captured"}
    process = subprocess.run(
        [sys.executable, str(tmp_path / "repro.py"), "--dry-run"],
        capture_output=True, text=True, timeout=20)
    assert process.returncode == 0, process.stderr
    payload = json.loads(process.stdout)
    assert payload["status"] == "dry_run"
    assert payload["failed_checks"] == []
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["schema"] == "mindie-single-op-repro-manifest/1"
    assert manifest["fidelity"] == result["fidelity"]
    assert manifest["checks"]["metadata_installable"] is True


def test_diff_trace_host_and_collective_scenarios():
    predicted = {"total_ms": 8, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 8}]}
    captured = {"total_ms": 9, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 8}],
        "gaps": [{"stream": 1, "start_ms": 8, "duration_ms": 1}]}
    host = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert host["buckets"]["host_dispatch_bubble_delta_ms"] == pytest.approx(1.0)
    assert host["host_bound_ratio"] == pytest.approx(1 / 9, rel=1e-6)
    predicted_comm = {"total_ms": 10, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 8},
        {"name": "AllReduce", "stream": 0, "start_ms": 8, "duration_ms": 2}]}
    captured_comm = {"total_ms": 11, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 8},
        {"name": "AllReduce", "stream": 0, "start_ms": 8, "duration_ms": 3}]}
    comm = attribute_diff(predicted_comm, captured_comm, launch_overhead_us=0)
    assert comm["buckets"]["collective_and_skew_delta_ms"] == pytest.approx(1.0)
    assert comm["conservation"]["exact"] is True


def test_effective_rows_and_pad_aware_cost():
    masked = effective_operator_rows("aclnnFlashAttentionVarLenScore", 48, 33,
                                     cann_version="8.0")
    assert masked["mode"] == "masked_varlen"
    assert masked["charged_tokens"] == 33
    assert masked["padded_tokens"] == 15
    full = effective_operator_rows("aclnnRmsNorm", 48, 33, cann_version="9.0")
    assert full["charged_tokens"] == 48
    grouped = effective_operator_rows(
        "aclnnGroupedMatmulV4", 64, None, {"group_list": [16, 32, 48, 64]},
        cann_version="9.0")
    assert grouped["charged_tokens"] == 64
    cost = pad_aware_operator_cost("aclnnGroupedMatmulV4", 6.4, 64, None,
                                   bound_args={"group_list": [16, 32, 48, 48]},
                                   cann_version="9.0")
    assert cost["duration_ms"] == pytest.approx(4.8)
    unknown = effective_operator_rows("mystery_op", 10, None)
    assert unknown["semantic_source"] == "unknown_operator"
    masked_cost = pad_aware_operator_cost("aclnnFlashAttentionVarLenScore", 10.0,
                                          48, 33, cann_version="8.0")
    assert masked_cost["duration_ms"] == 10.0
    assert masked_cost["work_model"] == "bucket_basis_unresolved"
    assert masked_cost["row_scaled_estimate_ms"] == pytest.approx(10.0 * 33 / 48)


def test_fabric_plan_and_synthetic_recovery():
    tier_ranks = {"intra_package_die": [0, 1],
                  "intra_node_hccs": list(range(8)),
                  "inter_node_roce": [0, 8]}
    plan = build_fabric_probe_plan(
        world_size=16, ranks_per_node=8, duration_s=60,
        topology={"tiers": [
            {"tier": "intra_package_die", "ranks": tier_ranks["intra_package_die"],
             "protocol": "HCCS"},
            {"tier": "intra_node_hccs", "ranks": tier_ranks["intra_node_hccs"],
             "protocol": "HCCS"},
            {"tier": "inter_node_roce", "ranks": tier_ranks["inter_node_roce"],
             "protocol": "RoCE"}]})
    validate_plan(plan)
    assert plan["status"] == "admitted"
    assert {tier["tier"] for tier in plan["tiers"]} == {
        "intra_package_die", "intra_node_hccs", "inter_node_roce"}
    script = emit_fabric_probe_script(plan)
    assert script["syntax_ok"] is True
    samples = []
    for tier, alpha, beta in (("intra_package_die", 2.0, 0.05),
                              ("intra_node_hccs", 8.0, 0.1),
                              ("inter_node_roce", 30.0, 0.55)):
        ranks = tier_ranks[tier]
        for op in ("all_reduce", "all_gather", "reduce_scatter", "all_to_all"):
            for size in (4096, 65536, 1048576):
                samples.append({"tier": tier, "op": op, "bytes": size,
                                "latency_us": alpha + beta * size / 1000.0,
                                "group_size": len(ranks), "group_ranks": ranks,
                                "rank": ranks[0], "validated": True,
                                "protocol": "RoCE" if tier == "inter_node_roce" else "HCCS"})
    profile = fit_calibrated_fabric_profile(plan, samples)
    assert profile["status"] == "calibrated"
    assert profile["topology_verified"] is True
    assert profile["usable_for_link_override"] is True
    assert profile["tiers"]["intra_node_hccs"]["operations"]["all_reduce"][
        "alpha_us"] == pytest.approx(8.0, rel=1e-6)
    assert profile["tiers"]["intra_node_hccs"]["operations"]["all_reduce"][
        "beta_ns_per_byte"] == pytest.approx(0.1, rel=1e-6)


def test_cli_inspect_op_and_repro_op(tmp_path):
    output = tmp_path / "card.json"
    assert profiler_main(["inspect-op", "aclnnPagedAttention", "--version", "8.0",
                          "--output", str(output)]) == 0
    card = json.loads(output.read_text())
    assert card["schema"] == "mindie-op-abi-card/2"
    binding_path = tmp_path / "binding.json"
    binding_path.write_text(json.dumps(paged_binding()))
    artifacts = tmp_path / "artifacts"
    assert profiler_main(["repro-op", "--row", str(binding_path),
                          "--output-dir", str(artifacts)]) == 0
    assert checked_io.path_exists(artifacts / "repro.py")
    assert checked_io.path_exists(artifacts / "manifest.json")


def test_r8_mutable_alias_recipe_uses_pristine_reset():
    binding = bind_captured_occurrence({
        "op_type": "aclnnApplyRotaryPosEmbV2", "cann_version": "9.0",
        "input_shapes": ["[4,8,128]"] * 4,
        "input_names": ["query_ref", "key_ref", "cos", "sin"],
        "input_dtypes": ["BF16"] * 4, "input_formats": ["ND"] * 4,
        "attrs": {"layout": 1, "rotary_mode": "half"}})
    assert binding["status"] == "bound"
    occurrence = _compact_occurrence(binding)
    assert occurrence["call_plan"]["mutable_aliases"] == ["query_ref", "key_ref"]
    result = generate_single_op_reproducer(binding)
    assert result["status"] == "ready"
    assert "_snapshot(inputs" in result["script"]
    assert "reset()" in result["script"]


def test_inspect_card_is_identity_complete():
    card = inspect_op_abi("aclnnFusedInferAttentionScoreV3", cann_version="9.0")
    assert card["card"]["signature"] == "aclnn_c_api"
    assert card["card"]["pinned"] is True
    assert card["card"]["complete"] is False  # no pinned V3 torch recipe
    assert card["identity"]["source_sha256"]


# ------------------------------------------------------------------- R1
def test_r1_parallel_stream_idle_is_zero_host_bubble():
    predicted = {"total_ms": 10, "ops": [{"name": "Matmul", "stream": 0,
                                          "start_ms": 0, "duration_ms": 10}]}
    captured = {"total_ms": 10, "ops": [{"name": "Matmul", "stream": 0,
                                         "start_ms": 0, "duration_ms": 10}],
                "gaps": [{"stream": 1, "start_ms": 0, "duration_ms": 5},
                         {"stream": 2, "start_ms": 0, "duration_ms": 5}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["buckets"]["host_dispatch_bubble_delta_ms"] == 0.0
    assert result["buckets"]["kernel_roofline_and_clock_delta_ms"] == 0.0
    assert result["host_bound_ratio"] == 0.0
    assert result["conservation"]["exact"] is True


def test_r1_parallel_duration_changes_are_not_double_counted():
    predicted = {"total_ms": 10, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 10},
        {"name": "Matmul", "stream": 1, "start_ms": 0, "duration_ms": 10}]}
    captured = {"total_ms": 11, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 11},
        {"name": "Matmul", "stream": 1, "start_ms": 0, "duration_ms": 11}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["buckets"]["kernel_roofline_and_clock_delta_ms"] == pytest.approx(1.0)
    assert result["kernel_roofline_and_clock"]["roofline_clock_explained_ms"] == pytest.approx(1.0)
    assert result["kernel_roofline_and_clock"]["unexplained_residual_ms"] == pytest.approx(0.0)


def test_r1_cast_under_matmul_has_zero_graph_delta():
    predicted = {"total_ms": 10, "ops": [{"name": "Matmul", "stream": 0,
                                          "start_ms": 0, "duration_ms": 10}]}
    captured = {"total_ms": 10, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 10},
        {"name": "Cast", "stream": 1, "start_ms": 0, "duration_ms": 2}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["buckets"]["graph_lowering_delta_ms"] == 0.0
    assert result["total_delta_ms"] == 0.0


def test_r1_matched_fallback_is_charged_once():
    predicted = {"total_ms": 10, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 8},
        {"name": "X", "stream": 0, "start_ms": 8, "duration_ms": 2}]}
    captured = {"total_ms": 11, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 8},
        {"name": "X", "stream": 0, "start_ms": 8, "duration_ms": 3,
         "fallback": True}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["buckets"]["graph_lowering_delta_ms"] == pytest.approx(1.0)
    assert result["buckets"]["kernel_roofline_and_clock_delta_ms"] == pytest.approx(0.0)


def test_r1_removed_op_is_a_negative_graph_delta():
    predicted = {"total_ms": 10, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 5},
        {"name": "B", "stream": 0, "start_ms": 5, "duration_ms": 5}]}
    captured = {"total_ms": 5, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 5}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["buckets"]["graph_lowering_delta_ms"] == pytest.approx(-5.0)
    assert result["status"] == "partial"
    assert result["conservation"]["exact"] is True


def test_r1_improvements_are_signed_not_clipped():
    predicted = {"total_ms": 10, "ops": [{"name": "Matmul", "stream": 0,
                                          "start_ms": 0, "duration_ms": 10}]}
    captured = {"total_ms": 8, "ops": [{"name": "Matmul", "stream": 0,
                                        "start_ms": 0, "duration_ms": 8}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["total_delta_ms"] == pytest.approx(-2.0)
    assert result["buckets"]["kernel_roofline_and_clock_delta_ms"] == pytest.approx(-2.0)
    assert result["conservation"]["exact"] is True


def test_r1_missing_evidence_is_partial_and_clock_is_never_assumed():
    result = attribute_diff({"total_ms": 10}, {"total_ms": 12})
    assert result["status"] == "partial"
    assert result["issues"]
    assert result["kernel_roofline_and_clock"]["clock_status"] == "unavailable"
    assert result["kernel_roofline_and_clock"]["nominal_aic_mhz"] is None
    assert result["kernel_roofline_and_clock"]["thermal_throttled"] is None


def test_r1_stages_are_ordered_and_sum_exactly():
    predicted = {"total_ms": 10, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 10}]}
    captured = {"total_ms": 12, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 10},
        {"name": "AllReduce", "stream": 0, "start_ms": 10, "duration_ms": 2}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    stages = result["stages"]
    assert [stages[key] for key in ("R0", "R1", "R2", "R3", "R4_model", "O")] == sorted(
        stages[key] for key in ("R0", "R1", "R2", "R3", "R4_model", "O"))
    assert result["buckets"]["collective_and_skew_delta_ms"] == pytest.approx(2.0)
    assert sum(result["buckets"].values()) == pytest.approx(result["total_delta_ms"])


# ------------------------------------------------------------------- R2
def test_r2_unknown_suffixes_never_prefix_match():
    assert catalog_operator("aclnnMatmulBogusV999") is None
    assert catalog_operator("aclnnFlashAttentionVarLenScoreV999") is None
    binding = bind_captured_occurrence({
        "op_type": "aclnnMatmulBogusV999", "cann_version": "9.2",
        "input_shapes": ["[2,2]", "[2,2]"]})
    assert binding["status"] == "unknown_abi"
    assert binding["raw_input_slots"] == 2
    assert binding["raw_evidence"]["inputs"]["slot_count"] == 2

def test_r2_missing_and_unverified_versions_are_unknown_abi():
    row = {"op_type": "aclnnMatmul", "input_shapes": ["[2,2]", "[2,2]"],
           "output_shapes": ["[2,2]"]}
    binding = bind_captured_occurrence(row)
    assert binding["status"] == "unknown_abi"
    assert binding["cann_version"] is None
    assert binding["issues"][0]["code"] == "unknown_abi_missing_cann_version"
    wrong = bind_captured_occurrence({**row, "cann_version": "9.9"})
    assert wrong["status"] == "unknown_abi"
    assert wrong["issues"][0]["code"] == "unknown_abi_unverified_cann_version"

def test_r2_sources_are_sha_pinned_and_flattening_is_declared():
    catalog = json.loads((Path(__file__).parents[1] / "mindie_profiler"
                          / "op_api_catalog.json").read_text())
    checked = 0
    for name, entry in catalog["operators"].items():
        adapter = entry["flatten_adapter"]
        assert adapter["rule"] and adapter["basis"]
        for source in entry["sources"]:
            if source.get("kind") in {"local_header", "local_header_markdown",
                                      "python_call_site"}:
                path = Path(source["path"])
                if not path.exists():
                    pytest.skip(f"external source checkout absent on runner: {path}")
                payload = path.read_bytes()
                assert "sha256:" + hashlib.sha256(payload).hexdigest() == source["sha256"]
                checked += 1
    assert checked >= 20
    assert catalog["source_pins"]["ops-transformer"]["head"].startswith("a3925fd49c")
    assert catalog["source_pins"]["vllm-ascend"]["head"].startswith("6e3299ab49")

def test_r2_surface_kinds_are_separated():
    catalog = json.loads((Path(__file__).parents[1] / "mindie_profiler"
                          / "op_api_catalog.json").read_text())
    for entry in catalog["operators"].values():
        assert entry["surface"] in {"aclnn_c_api", "torch_npu_op", "vllm_ascend_op",
                                    "hccl_collective"}
        assert "c_abi_slots" in entry and "repro_recipe" in entry
        assert entry["c_abi_slots"]["kind"] in {"aclnn_c_api", "torch_schema"}

# ------------------------------------------------------------------- R3
def _parse_header_signature(path: Path, symbol: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\b" + re.escape(symbol) + r"\s*\(", text)
    assert match, symbol
    index, depth = match.end(), 1
    while depth:
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
        index += 1
    body = text[match.end():index - 1]
    parts, depth, current = [], 0, ""
    for char in body:
        if char in "([<":
            depth += 1
        elif char in ")]>":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)
    return [re.split(r"[\s*]+", part.strip())[-1] for part in parts]

def test_r3_every_pinned_c_signature_matches_its_header():
    catalog = json.loads((Path(__file__).parents[1] / "mindie_profiler"
                          / "op_api_catalog.json").read_text())
    checked = 0
    for name, entry in catalog["operators"].items():
        source = entry["sources"][0]
        if source.get("kind") not in {"local_header", "local_header_markdown"}:
            continue
        header_path = Path(source["path"])
        if not header_path.exists():
            pytest.skip(f"external header checkout absent on runner: {header_path}")
        expected = _parse_header_signature(header_path, source["symbol"])
        actual = [param["c_name"] for param in entry["c_abi_slots"]["parameters"]]
        assert actual == expected, name
        checked += 1
    assert checked == 15

def test_r3_audited_arity_and_order():
    fa = catalog_entry("aclnnFlashAttentionVarLenScore")["c_abi_slots"]
    assert len(fa["input_slots"]) == 7
    assert [item["name"] for item in fa["slot_specs"]["outputs"]] == [
        "softmax_max_out", "softmax_sum_out", "softmax_out_out", "attention_out_out"]
    fia3 = catalog_entry("aclnnFusedInferAttentionScoreV3")["c_abi_slots"]
    assert len(fia3["input_slots"]) == 24
    assert fia3["input_slots"][-3:] == ["query_rope", "key_rope",
                                        "key_rope_antiquant_scale"]
    assert fia3["parameters"][1]["cat"] == "tensor_list"
    qli = catalog_entry("QuantLightningIndexer")["c_abi_slots"]
    assert qli["input_slots"][:5] == ["query", "key", "weights",
                                      "query_dequant_scale", "key_dequant_scale"]
    assert len(qli["output_slots"]) == 1
    rope_v2 = catalog_entry("aclnnApplyRotaryPosEmbV2")["c_abi_slots"]
    assert len(rope_v2["input_slots"]) == 4
    assert "actual_seq_lens" not in rope_v2["input_slots"]
    assert "rotary_mode" in rope_v2["attr_slots"]
    gmm = catalog_entry("aclnnGroupedMatmulV4")["c_abi_slots"]
    assert gmm["input_slots"][-1] == "activation_quant_offset"
    assert len(gmm["input_slots"]) == 12 and len(gmm["output_slots"]) == 3
    swiglu = catalog_entry("GroupedMatmulSwigluQuant")["c_abi_slots"]
    assert "x_scale" in swiglu["input_slots"]
    assert len(swiglu["output_slots"]) == 3
    routing = catalog_entry("MoeInitRoutingV2")["c_abi_slots"]
    assert len(routing["input_slots"]) == 2
    assert routing["output_slots"][-1] == "expert_tokens_before_capacity_out"
    finalize = catalog_entry("MoeFinalizeRoutingV2")["c_abi_slots"]
    assert "group_list" not in finalize["input_slots"]
    assert finalize["slot_specs"]["inputs"][6]["optional"] is True
    dispatch = catalog_entry("MoeDistributeDispatchV3")["c_abi_slots"]
    assert len(dispatch["input_slots"]) == 6 and len(dispatch["output_slots"]) == 7
    combine = catalog_entry("MoeDistributeCombineV3")["c_abi_slots"]
    assert len(combine["input_slots"]) == 17
    assert combine["slot_specs"]["inputs"][4]["optional"] is False
    mla = catalog_entry("MlaPrologV2")["c_abi_slots"]
    assert len(mla["input_slots"]) == 19 and len(mla["output_slots"]) == 3
    assert mla["input_slots"][-1] == "smooth_scales_cq"
    assert catalog_entry("aclnnMatmul")["c_abi_slots"]["kind"] == "aclnn_c_api"
    assert catalog_entry("QuantBatchMatmulV3")["c_abi_slots"]["kind"] == "torch_schema"

def test_r3_recipes_are_capability_qualified():
    for name in operator_names():
        entry = catalog_entry(name)
        recipe = entry["repro_recipe"]
        if not recipe["supported"]:
            assert recipe["unsupported_reason"], name
        if recipe["multi_rank_required"]:
            assert entry["surface"] in {"hccl_collective", "aclnn_c_api"}
        if recipe["status"] != "ready":
            continue
        for reference in recipe["keyword"].values():
            for kind, value in reference.items():
                if kind in {"input", "output", "list"}:
                    all_slots = (entry["c_abi_slots"]["input_slots"]
                                 + entry["c_abi_slots"]["output_slots"])
                    assert value in all_slots, (name, value)
    paged = catalog_entry("aclnnPagedAttention")["repro_recipe"]
    assert paged["output_buffers"] == ["out"]
    assert paged["keyword"]["out"] == {"output": "out"}
    for name in operator_names():
        recipe = catalog_entry(name)["repro_recipe"]
        if recipe["status"] == "ready":
            assert recipe["repro_supported"] is True
            assert recipe["signature"]["verified"] is True
        else:
            assert recipe["repro_supported"] is False
            assert recipe["unsupported_reason"]

# ------------------------------------------------------------- R4 / R5
def test_r4_middle_hole_is_preserved_not_collapsed():
    row = fa_row(input_shapes=["[2,2]", "", "[2]"] + ["[2]"] * 4,
                 input_dtypes=["BF16", "", "BF16"] + ["BF16"] * 4,
                 input_formats=["ND", "", "ND"] + ["ND"] * 4)
    parsed = slot_descriptors(row, "input")
    assert len(parsed["slots"]) == 7
    assert parsed["slots"][1]["state"] == "absent"
    assert parsed["slots"][2]["state"] == "tensor"

def test_r4_extra_outputs_are_conserved_and_block_repro():
    binding = bind_captured_occurrence({
        "op_type": "aclnnMatmul", "cann_version": "9.2",
        "input_shapes": ["[2,2]", "[2,2]"],
        "input_dtypes": ["BF16", "BF16"], "input_formats": ["ND", "ND"],
        "output_shapes": ["[2,2]", "[2,2]", "[2,2]"],
        "output_dtypes": ["BF16"] * 3, "output_formats": ["ND"] * 3})
    assert binding["status"] == "incomplete"
    codes = [issue["code"] for issue in binding["issues"]]
    assert "unexpected_output_slots" in codes
    extras = next(issue for issue in binding["issues"]
                  if issue["code"] == "unexpected_output_slots")
    assert len(extras["slots"]) == 2
    assert extras["slots"][0]["shape"] == [2, 2]
    with pytest.raises(ProfilerUsageError):
        generate_single_op_reproducer(binding)

def test_r4_extra_inputs_are_conserved():
    binding = bind_captured_occurrence(fa_row(
        input_shapes=["[48,8,128]"] * 8,
        input_dtypes=["BF16"] * 8, input_formats=["ND"] * 8))
    assert binding["status"] == "incomplete"
    extras = next(issue for issue in binding["issues"]
                  if issue["code"] == "unexpected_input_slots")
    assert extras["count"] == 1 and extras["slots"][0]["shape"] == [48, 8, 128]

def test_r4_missing_shapes_keep_dtype_and_layout_columns():
    binding = bind_captured_occurrence({
        "op_type": "aclnnMatmul", "cann_version": "9.2",
        "input_dtypes": ["BF16", "BF16"], "input_formats": ["ND", "ND"],
        "output_shapes": ["[2,2]"]})
    assert binding["status"] != "bound"
    assert binding["raw_input_slots"] == 2
    assert len(binding["inputs"]) == 2
    assert all(record["state"] == "missing" for record in binding["inputs"])
    assert [record["dtype"] for record in binding["inputs"]] == ["bf16", "bf16"]
    assert [record["layout"] for record in binding["inputs"]] == ["ND", "ND"]

def test_r4_mixed_mapping_sequence_is_invalid_not_a_crash():
    parsed = slot_descriptors({"input_shapes": [
        {"shape": [2, 2], "dtype": "BF16", "layout": "ND"}, "[2,2]"]}, "input")
    assert parsed["issues"][0]["code"] == "descriptor_not_a_mapping"
    assert parsed["slots"][1]["state"] == "invalid"

def test_r5_states_absent_undefined_missing_invalid_scalar_tensor():
    assert parse_shape("") == (None, "missing")
    assert parse_shape("NULL") == (None, "missing")
    assert parse_shape("[]") == ([], "scalar")
    assert parse_shape("[0,2]") == ([0, 2], "tensor")
    assert parse_shape("[-1,2]") == ([-1, 2], "invalid")
    row = fa_row(input_shapes=["[2,2]", "[]", "[0,2]", "[-1,2]", "",
                               "[2,2]", "[2,2]"],
                 input_dtypes=["DT_UNDEFINED", "BF16", "BF16", "BF16", "",
                               "BF16", "BF16"],
                 input_formats=["NULL", "ND", "ND", "ND", "", "ND", "ND"])
    parsed = slot_descriptors(row, "input")
    assert [slot["state"] for slot in parsed["slots"]] == [
        "missing", "scalar", "tensor", "invalid", "absent", "tensor", "tensor"]

def test_r5_invalid_shape_never_becomes_a_scalar():
    binding = bind_captured_occurrence({
        "op_type": "aclnnMatmul", "cann_version": "9.2",
        "input_shapes": ["[-1,2]", "[2,2]"],
        "input_dtypes": ["BF16", "BF16"], "input_formats": ["ND", "ND"],
        "output_shapes": ["[2,2]"], "output_dtypes": ["BF16"],
        "output_formats": ["ND"]})
    first = binding["inputs"][0]
    assert first["state"] == "invalid" and first["shape"] == [-1, 2]
    assert binding["status"] != "bound"

def test_r5_undefined_slot_is_distinct_and_not_allocated():
    row = fa_row(input_shapes=["[]", "[2,2]", "[2,2]", "[2,2]", "[2,2]", "[2,2]",
                              "[2,2]"],
                 input_dtypes=["DT_UNDEFINED", "BF16", "BF16", "BF16", "BF16",
                               "BF16", "BF16"],
                 input_formats=["NULL", "ND", "ND", "ND", "ND", "ND", "ND"])
    binding = bind_captured_occurrence(row)
    first = binding["inputs"][0]
    assert first["state"] == "undefined"
    assert first["present"] is False
    assert first["dtype_raw"] == "DT_UNDEFINED"
    assert first["layout_raw"] == "NULL"
    assert binding["status"] == "incomplete"

def test_r5_unknown_dtype_literal_blocks_binding():
    row = fa_row(input_dtypes=["MYSTERY", "BF16", "BF16", "BF16", "BF16", "BF16",
                               "BF16"])
    binding = bind_captured_occurrence(row)
    assert binding["status"] == "incomplete"
    assert "dtype_unknown" in [issue["code"] for issue in binding["issues"]]
    assert binding["inputs"][0]["dtype_raw"] == "MYSTERY"

def test_r5_required_attr_with_none_is_absent():
    row = fa_row(attrs={**fa_row()["attrs"], "num_heads": None})
    binding = bind_captured_occurrence(row)
    assert "required_attrs_absent" in [issue["code"] for issue in binding["issues"]]
    assert "head_num" in next(issue for issue in binding["issues"]
                              if issue["code"] == "required_attrs_absent")["names"]

# ------------------------------------------------------------------- R6
def test_r6_bsh_uses_the_batch_axis():
    row = fa_row(input_shapes=["[2,64,128]"] * 7,
                 attrs={**fa_row()["attrs"], "input_layout": "BSH",
                        "actual_seq_q_len": [10, 20],
                        "actual_seq_kv_len": [10, 20]})
    binding = bind_captured_occurrence(row)
    assert binding["padding"]["bucket_tokens"] == 2 * 64
    assert binding["padding"]["logical_tokens"] == 30
    assert binding["padding"]["effective_tokens"] == 30

def test_r6_tnd_tail_rule_is_device_qualified():
    row = fa_row(attrs={**fa_row()["attrs"], "device": "arch22"})
    binding = bind_captured_occurrence(row)
    codes = [violation["code"] for violation in binding["padding"]["violations"]]
    assert "sequence_tail_not_equal_bucket" in codes
    generic = bind_captured_occurrence(fa_row())
    assert "sequence_tail_not_equal_bucket" not in [
        violation["code"] for violation in generic["padding"]["violations"]]

def test_r6_pa_and_non_pa_kv_encoding_are_distinct():
    row = {"op_type": "aclnnFusedInferAttentionScoreV2", "cann_version": "9.0",
           "input_shapes": ["[16,8,128]", "[16,128]", "[16,128]"],
           "input_names": ["query", "key", "value"],
           "input_dtypes": ["BF16"] * 3, "input_formats": ["ND"] * 3,
           "output_shapes": ["[16,8,128]"], "output_names": ["attention_out"],
           "output_dtypes": ["BF16"], "output_formats": ["ND"],
           "attrs": {"input_layout": "TND", "num_heads": 8,
                     "num_key_value_heads": 8, "scale_value": 0.088,
                     "block_table": [[0, 1]], "actual_seq_lengths": [16],
                     "actual_seq_lengths_kv": [16, 8]}}
    binding = bind_captured_occurrence(row)
    assert binding["padding"]["qualification"]["pa"] is True
    assert binding["padding"]["qualification"]["kv_mode"] == {
        "PA": "lengths", "non_PA": "cumsum"}

def test_r6_group_list_types_validate_exactly():
    bad = validate_group_list([32, 30, 73], 0, 128)
    assert not bad["valid"]
    assert {item["code"] for item in bad["violations"]} >= {
        "group_list_not_monotone"}
    out_of_bounds = validate_group_list([32, 64, 200], 0, 128)
    assert any(item["code"] == "group_list_out_of_bounds"
               for item in out_of_bounds["violations"])
    counts = validate_group_list([32, 0, 41], 1, 128)
    assert counts["routed_tokens"] == 73 and counts["valid"]
    pairs = validate_group_list([0, 32, 1, 41], 2, 128, num_groups=4)
    assert pairs["routed_tokens"] == 73 and pairs["valid"]
    assert not validate_group_list([0, 32, 1], 2, 128)["valid"]

def test_r6_effective_zero_is_not_replaced_by_the_bucket():
    row = fa_row(attrs={**fa_row()["attrs"], "effective_tokens": 0})
    binding = bind_captured_occurrence(row)
    assert binding["padding"]["effective_tokens"] == 0
    assert binding["padding"]["logical_tokens"] == 0
    assert binding["padding"]["charged_tokens"] == 0

def test_r6_leading_zero_offsets_are_emitted_and_checked():
    assert synthesize_offsets([10, 20], cumulative=True, leading_zero=True) == [0, 10, 30]
    assert synthesize_offsets([10, 20], cumulative=False) == [10, 20]
    row = fa_row(attrs={**fa_row()["attrs"], "actual_seq_q_len": [0, 33],
                        "actual_seq_kv_len": [0, 33]})
    binding = bind_captured_occurrence(row)
    assert binding["padding"]["effective_tokens"] == 33
    assert binding["padding"]["logical_tokens"] == 33

def test_r6_group_count_comes_from_the_allocated_tensor():
    values = synthesize_group_list(48, 3, 0)
    assert len(values) == 3 and values[-1] == 48
    assert synthesize_group_list(48, 3, 1) == [16, 16, 16]
    assert synthesize_group_list(48, 3, 2) == [0, 16, 1, 16, 2, 16]

