"""Acceptance tests for standalone native-primitive workload integration.

[Role]
  Pin the normal entry contract used by the fleet caller (``None`` only outside
  a genuine primitive workload), source-descriptor geometry for the 29
  calibration captures, per-call versus fabricated forward-population
  boundaries, and measurement independence of the physical program.

[Invariants]
  * Prediction never changes when row-carried timings or kernel summaries are
    perturbed; the descriptor path and geometry are the only inputs.
  * FIA/GDN/conv1d/MoE workloads are priced as one standalone native call and
    are not expanded into a model body or 32 decode forwards.
  * An applicable call without a retained descriptor returns an explicit
    unsupported record with missing facts instead of a guessed number.

[Timeouts & Locks]
  Small local JSON/CSV reads; the full 29-row sweep is bounded and offline.

[Side-Effect Policy]
  Read-only; no devices, subprocesses or repository writes.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
_STRUCTURE = ROOT / "examples" / "structure"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(_STRUCTURE) not in sys.path:
    sys.path.insert(0, str(_STRUCTURE))

from fleet_primitive_workloads import (  # noqa: E402
    DESCRIPTOR_SCHEMA,
    MOE_NATIVE_ROLES,
    SCHEMA,
    SUITE,
    PrimitiveWorkload,
    declared_primitive_workload,
    native_call_artifact,
    is_primitive_workload,
    predict_primitive_workload,
    primitive_native_observation,
    primitive_workload_descriptor,
)

FLEET_SOURCE = Path(os.environ.get(
    "MINDIE_FLEET_CAPTURES_PATH",
    "/tmp/mindie-sim-profiling-bench/data/fleet_captures.jsonl",
))
CALIBRATION_LINEAGE = "calibration-20261107/a5/"


def _rows() -> list[dict]:
    if not FLEET_SOURCE.is_file():
        pytest.skip("fleet capture archive is not available")
    rows = []
    with FLEET_SOURCE.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("suite") == SUITE:
                rows.append(row)
    assert len(rows) == 29
    return rows


def _by_fragment(rows: list[dict], fragment: str) -> dict:
    matches = [row for row in rows if fragment in row["capture_id"]]
    assert len(matches) == 1, (fragment, len(matches))
    return matches[0]


def _sha(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _plain_row() -> dict:
    return {
        "suite": "a5_multinode_full_coverage_20261108",
        "capture_id": "a5_multinode_20261108:case:cell",
        "observed_ms": 1.0,
        "geometry": {"structural_weights": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]},
    }


def test_non_primitive_rows_return_none_and_do_not_price():
    assert predict_primitive_workload(_plain_row()) is None
    assert primitive_workload_descriptor(_plain_row()) is None
    assert declared_primitive_workload(_plain_row()) is None
    assert is_primitive_workload(_plain_row()) is False
    # A calibration-suite tag alone is not a primitive boundary.
    disguised = {
        "suite": SUITE,
        "capture_id": "operator_and_kernel_calibration_20261107:unknown",
    }
    assert predict_primitive_workload(disguised) is None


def test_all_29_calibration_captures_are_resolved_and_priced_or_explained():
    rows = _rows()
    kinds = {}
    for row in rows:
        assert is_primitive_workload(row) is True
        descriptor = primitive_workload_descriptor(row)
        assert descriptor is not None, row["capture_id"]
        declared = declared_primitive_workload(row)
        assert isinstance(declared, PrimitiveWorkload)
        assert declared.to_dict()["source"] == descriptor["source"]
        assert declared.repeats == descriptor["repeats"]
        assert descriptor["schema"] == DESCRIPTOR_SCHEMA
        assert descriptor["repeats"] in (3, None)
        assert descriptor["hardware"]["sku"] == "Ascend950DT_9582"
        kinds[descriptor["kind"]] = kinds.get(descriptor["kind"], 0) + 1
        result = predict_primitive_workload(row)
        assert result is not None
        assert result["schema"] == SCHEMA
        assert result["descriptor"]["source"]["capture_path"]
        assert result["capture_id"] == row["capture_id"]
        assert result["prediction_boundary"] == "native_calls"
        assert result["boundary_basis"] == "elapsed_native_call_span_ms"
        if result["status"] == "predicted":
            assert result["predicted_ms"] > 0
            assert result["predicted_total_ms"] == pytest.approx(
                result["predicted_ms"] * result["repeats"])
            assert result["program"]["kernels"]
            assert all(kernel["duration_ms"] >= 0
                       for kernel in result["program"]["kernels"])
            samples = result["boundary_samples"]
            assert len(samples) == result["repeats"] == 3
            assert [sample["key"] for sample in samples] == [
                f"{row['capture_id']}:call{index}" for index in range(3)]
            assert all(sample["boundary_ms"] == result["predicted_ms"]
                       for sample in samples)
            assert all(sample["boundary_ms"] != result["predicted_total_ms"]
                       for sample in samples)
            artifact = native_call_artifact(result["descriptor"])
            assert artifact is not None and artifact.is_file()
            assert result["source_sha256"] == _sha(artifact)
        else:
            assert result["status"].startswith("unsupported")
            assert result["unsupported"]["missing_facts"]
            assert result["boundary_samples"] == []
            assert result["predicted_ms"] is None
    # The raw campaign declares eight FIA/GDN/conv1d probes and 21 MoE probes.
    assert kinds.get("fia_prefill") == 4  # two full prefill + two chunked calls
    assert kinds.get("fia_decode") == 2
    assert kinds.get("gdn_chunk_prefill") == 1
    assert kinds.get("causal_conv1d") == 1
    assert kinds.get("moe_native_chain") == 20
    assert kinds.get("moe_native_unresolved") == 1


def test_conv1d_uses_source_bias_false_and_prices_the_native_call():
    rows = _rows()
    row = _by_fragment(rows, "conv1d_T8192_35b_tp4")
    result = predict_primitive_workload(row)
    assert result["status"] == "predicted"
    assert result["repeats"] == 3
    assert result["predicted_ms"] == pytest.approx(0.03834213636365778, rel=1e-6)
    assert result["diagnostics"]["relative_error"] == pytest.approx(
        result["predicted_ms"] / 0.038358 - 1.0, rel=1e-6)
    assert result["descriptor"]["tensors"]["bias"] is False


def test_fia_capture_provenance_and_retained_dispatch():
    """Pin the actual 35B FIA capture ABI, source hashes and block dispatch.

    These are source identities, not timing goldens: the handoff, native-source
    manifest, raw kernel rows and the adapter's declared ABI must agree.  The
    CANN FIA library bytes are not retained; that missing binary identity is
    explicit and must not be guessed.
    """
    rows = _rows()
    row = _by_fragment(rows, "fia_prefill_q8192_35b_tp4")
    descriptor = primitive_workload_descriptor(row)
    source = descriptor["source"]
    assert source["host_ip"] == "177.31.28.1"
    assert source["host_name"] == "rack08os8"
    assert source["chip"] == "Ascend950DT"
    assert source["container"] == "ylf_pro0813_20261025"
    assert "v0.30.0-a5-cann9.2.0_20261022115200-20261024-r35" in source["image"]
    assert source["versions"]["torch"] == "2.10.0+cpu"
    assert source["versions"]["torch_npu"] == "2.10.0.post7"
    assert source["versions"]["npu_smi"] == "26.2.0.b020"
    native = json.loads(Path(source["native_sources_path"]).read_bytes())
    assert source["native_sources_sha256"] == _sha(Path(source["native_sources_path"]))
    assert source["native_source_files"] == native["sha256"]
    assert source["native_source_files"][
        "/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py"
    ] == "bea4e410f797557e29cedbb495024147606e74b0e056d725194760ca69296eba"
    tensors = descriptor["tensors"]
    assert (tensors["q_len"], tensors["kv_len"]) == (8192, 8192)
    assert (tensors["query_heads"], tensors["kv_heads"], tensors["head_dim"]) == (
        4, 1, 256)
    assert tensors["input_layout"] == "TND"
    assert tensors["sparse_mode"] == 3
    assert tensors["pre_tokens"] == 2147483647
    assert tensors["next_tokens"] == 0
    assert tensors["op_api"] == "torch_npu.npu_fused_infer_attention_score"
    assert source["declared_device"] == 0
    assert source["raw_kernel_device_id"] == 1
    assert source["device_identity_status"] == "unresolved_logical_vs_raw"
    profiling = source["profiling_artifacts"]
    assert profiling["files"] == ["kernel_details.csv"]
    assert profiling["has_kernel_details_csv"] is True
    assert profiling["has_analysis_db"] is False
    assert profiling["has_trace_view"] is False
    assert profiling["has_op_summary"] is False
    dispatch = tensors["device_dispatch"]
    assert dispatch["status"] == "retained_raw_dispatch"
    assert dispatch["primary_name"] == "FusedInferAttentionScore"
    assert (dispatch["block_num"], dispatch["mix_block_num"]) == (32, 64)
    assert dispatch["row_count"] == 3
    artifact = native_call_artifact(descriptor)
    assert artifact is not None
    assert dispatch["sha256"] == _sha(artifact)
    assert source["binary_sha256"] == (
        "eb1c788e39b7a02f0694450e917a3771c7e65d7d8fb9ea2e03f78c4a5313c456")
    assert source["binary_path"] == (
        "usr/local/Ascend/cann-9.2.0/aarch64-linux/lib64/libopapi.so")
    assert source["binary_size_bytes"] == 49775024
    assert source["binary_role"] == "cann_opapi_library"
    assert source["binary_identity_status"] == (
        "image_layer_binary_hash_source_files_verified")
    assert source["capture_dispatch_origin"] == "direct_torch_npu_op_api_probe"
    assert "next_tokens=0" in source["capture_api_signature"]
    assert source["model_dispatcher_source"]["sha256"] == (
        "bea4e410f797557e29cedbb495024147606e74b0e056d725194760ca69296eba")
    assert source["model_dispatcher_used_for_pricing"] is False
    cann = source["cann_fia_kernel_sources"]
    assert cann["fia_arch35_template_tiling_key_enum.h"] == (
        "48d2b245322504291a7606003afa12e0094bd171f5a908dcdcbad74a7687ba16")
    assert cann["fused_infer_attention_score_template_tiling_key.h"] == (
        "2ef47d10a40eb1d5133d8c923fc3a67af4dd8da450a4b701b438e55df7164cc8")
    assert cann["fia_template_dispatcher.h"] == (
        "dc1f808865d822ffa89ecd6e965e869d8211a3ff4768ed105b54a7ce73f86034")
    assert cann["matching_configs"]["D128_64x256"]["config"] == 1
    assert cann["matching_configs"]["D128_128x128"]["config"] == 3
    assert cann["matching_configs"]["D256_128x128"]["config"] == 6
    assert cann["matching_configs"]["D256_64x256"]["config"] == 18
    assert cann["blanket_prefill_isfd_zero"] is False
    assert cann["selector_blocks"]["1266-1280"]["isfd"] == "false,true"
    assert cann["selector_blocks"]["1321-1334"]["isfd"] == "true"
    assert cann["selector_blocks"]["1335-1349"]["isfd"] == "true"
    assert cann["selector_blocks"]["1350-1362"]["isfd"] == "false"
    assert cann["selector_blocks"]["1363-1375"]["isfd"] == "false"
    assert cann["compile_time_fd"]["line"] == 797
    assert cann["compile_time_fd"]["text"] == "if constexpr (FLASH_DECODE)"
    op, _, _ = __import__("fleet_primitive_workloads")._fia_op(descriptor)
    metadata = dict(op.metadata)
    assert metadata["capture_abi"]["input_layout"] == "TND"
    assert metadata["capture_abi"]["sparse_mode"] == 3
    assert metadata["capture_abi"]["pre_tokens"] == 2147483647
    assert metadata["device_dispatch"]["block_num"] == 32


def test_fia_capture_contract_is_not_silently_remapped():
    rows = _rows()
    row = _by_fragment(rows, "fia_prefill_q8192_35b_tp4")
    descriptor = primitive_workload_descriptor(row)
    module = __import__("fleet_primitive_workloads")
    for field, value in (("input_layout", "BNSD"), ("sparse_mode", 4),
                         ("pre_tokens", 1), ("next_tokens", 8),
                         ("op_api", "torch_npu.npu_fused_infer_attention_score_v2")):
        changed = copy.deepcopy(descriptor)
        changed["tensors"][field] = value
        with pytest.raises(ValueError):
            module._fia_op(changed)


def test_fia_prefill_uses_the_true_staged_program_not_an_envelope():
    """Small causal counterfactuals must reproduce the public staged program.

    The four (q, kv) points are the source-matched small causal declarations
    used to reject the old aggregate-work envelope.  The adapter must equal the
    normal ``call_costs``/``StagedGQAPrefill`` result exactly, including when
    the same declared tensors are repeated.
    """
    from mindie_sim.prediction.call import call_costs
    from mindie_sim.prediction.mechanism import PlannedRecipe
    from mindie_sim.prediction.program import RecipeBook

    rows = _rows()
    row = _by_fragment(rows, "fia_prefill_q8192_35b_tp4")
    descriptor = primitive_workload_descriptor(row)
    assert descriptor["tensors"]["head_dim"] == 256
    # Historical literal .013457575757575765 differs from the executed
    # binary64 .013457575757575764 by 1 ULP; it is intentionally not asserted.
    # Independent execution identity + exact adapter/direct equality replaces it.
    for q_len, kv_len in ((32, 96), (65, 129), (129, 1024), (256, 2048)):
        changed = copy.deepcopy(descriptor)
        changed["tensors"]["q_len"] = q_len
        changed["tensors"]["kv_len"] = kv_len
        priced = __import__("fleet_primitive_workloads")._price_fia(changed)
        assert priced["composition"]["program"] == "staged_gqa_prefill_pipeline"
        assert priced["predicted_ms"] > 0
        op, recipe_name, build = __import__(
            "fleet_primitive_workloads")._fia_op(changed)
        direct = call_costs(
            __import__("fleet_primitive_workloads")._hardware_case(4),
            (op,),
            recipes=RecipeBook({recipe_name: PlannedRecipe(build)}),
            invocations=1,
        )
        assert priced["predicted_ms"] == direct["duration_ms"]


def test_chunked_fia_is_one_call_not_thirty_two_forwards():
    rows = _rows()
    row = _by_fragment(rows, "fia_chunked_q8192_kv400000_35b_tp4")
    result = predict_primitive_workload(row)
    assert result["status"] == "predicted"
    assert result["repeats"] == 3
    descriptor = result["descriptor"]
    assert descriptor["tensors"]["q_len"] == 8192
    assert descriptor["tensors"]["kv_len"] == 400000
    assert descriptor["tensors"]["query_heads"] == 4
    assert descriptor["tensors"]["kv_heads"] == 1
    assert descriptor["tensors"]["head_dim"] == 256
    # The fabricated row treats three actual calls (140.353362 ms total) as 32
    # decode forwards and reports 4.386 ms.  The primitive boundary is one call
    # of ~46.78 ms, and the reported total must keep the three real repeats.
    assert result["predicted_ms"] > 10.0
    assert result["predicted_total_ms"] > 30.0
    stages = result["program"]["kernels"][0]["stage_work"]
    assert {stage["stage"] for stage in stages} == {
        "q_load", "kv_load", "qk_pv", "softmax_online", "store"}
    assert all(stage["service_ms"] > 0 for stage in stages)
    assert all(stage["operation_count"] for stage in stages)
    observation = primitive_native_observation(row)
    assert observation["scope"] == "per_standalone_native_call"
    assert observation["per_call_ms"] == pytest.approx(
        sum(role["per_call_us"] for role in observation["roles"]) / 1000.0)
    scopes = result["comparison_scopes"]
    assert scopes["per_native_call"]["predicted_ms"] == result["predicted_ms"]
    assert scopes["profiled_repeat_total"]["predicted_ms"] == result["predicted_total_ms"]
    assert scopes["row_forward_population"]["usable"] is False
    assert observation["per_call_ms"] == pytest.approx(
        140.353362 / 3, rel=1e-3)
    assert observation["used_in_prediction"] is False


def test_target_timing_and_kernel_summary_perturbations_cannot_change_prediction():
    rows = _rows()
    for fragment in ("fia_prefill_q8192_35b_tp4", "gate3-final_e128k8_q4096_native",
                     "gdn_T8192_35b_tp4"):
        row = _by_fragment(rows, fragment)
        baseline = predict_primitive_workload(row)
        assert baseline["status"] == "predicted"
        poisoned = copy.deepcopy(row)
        poisoned["observed_ms"] = 1e9
        poisoned["predicted_ms"] = 1e-9
        poisoned["relative_error"] = 99.0
        poisoned["operator_modeling"] = {"predicted_operator_ms": 1e9}
        poisoned["kernel_summary"] = {
            "total_kernel_duration_us": 1e12,
            "top_op_types": [{"type": "fabricated", "total_us": 1e12}],
        }
        poisoned["geometry"] = {"active_hbm_mb": 1e12,
                                "structural_weights": [1, 0, 0, 0, 0, 0]}
        changed = predict_primitive_workload(poisoned)
        assert changed["predicted_ms"] == baseline["predicted_ms"]
        assert changed["predicted_total_ms"] == baseline["predicted_total_ms"]
        assert [k["duration_ms"] for k in changed["program"]["kernels"]] == [
            k["duration_ms"] for k in baseline["program"]["kernels"]]


def test_moe_native_chain_covers_the_declared_native_roles():
    rows = _rows()
    row = _by_fragment(rows, "gate3-final3_e16k4_q4096_native")
    result = predict_primitive_workload(row)
    assert result["status"] == "predicted"
    roles = [kernel["role"] for kernel in result["program"]["kernels"]]
    assert set(MOE_NATIVE_ROLES) <= set(roles)
    descriptor = result["descriptor"]
    tensors = descriptor["tensors"]
    assert (tensors["experts"], tensors["top_k"], tensors["local_bank"]) == (16, 4, 4)
    assert (tensors["hidden"], tensors["intermediate"]) == (2048, 768)
    assert descriptor["source"]["descriptor_sha256"]
    observation = primitive_native_observation(row)
    assert observation["status"] == "observed"
    assert observation["used_in_prediction"] is False
    assert observation["per_call_ms"] > 0
    diagnostics = result["diagnostics"]
    assert diagnostics["prediction_used_observation"] is False
    assert diagnostics["observed_ms"] == pytest.approx(observation["per_call_ms"])
    assert len(diagnostics["per_role"]) >= len(MOE_NATIVE_ROLES) - 1


def test_missing_moe_descriptor_is_unsupported_not_guessed():
    rows = _rows()
    row = _by_fragment(rows, "probe_fp32")
    result = predict_primitive_workload(row)
    assert result["status"] == "unsupported"
    assert result["predicted_ms"] is None
    assert result["unsupported"]["reason"] == "missing_declared_tensor_descriptor"
    assert "declared_E_K_bank_H_I_capacity_q" in result["unsupported"]["missing_facts"]


def test_unsupported_source_point_keeps_the_capture_in_inventory():
    rows = _rows()
    row = _by_fragment(rows, "gate3_e16k4_q4096_native")
    descriptor = primitive_workload_descriptor(row)
    assert descriptor is not None
    result = predict_primitive_workload(row)
    assert result["status"] == "unsupported"
    assert result["descriptor"]["source"]["status"] != "valid"
    # An unsupported capture must remain addressable by its exact source path.
    assert result["descriptor"]["source"]["descriptor_path"].endswith(".json")
