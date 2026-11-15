"""Round-2 closure: direct regressions for R1..R8 counterexamples.

[Role]
  Every assertion here is falsifiable by the specific Round-2 finding: replay
  double counting and misattribution, release-list certification, callable
  schema drift, tensor-list over-consumption, mapping-column loss, sequence
  metadata validity, paged value substitution, fidelity labelling and storage
  preservation.

[Invariants]
  * Identical traces reconcile at exactly the same makespan at R0..R4.
  * Serial duration growth is 100% ``op_delta`` and zero graph/schedule.
  * Every generated ready call plan binds against an ``inspect.Signature``
    stub built from the catalog's exact wrapper parameter names.
  * Captured invalid page/context values are installed and checked, never
    silently replaced by synthetic values that would pass.

[Timeouts & Locks]
  Pure in-memory work; no NPU, subprocess or distributed job.

[Side-Effect Policy]
  No writes; the paged/repro tests only build dictionaries and scripts in memory.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
from mindie_profiler import repro_atomic_io as checked_io

import pytest

from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.op_abi_binding import bind_resolved_occurrence
from mindie_profiler.op_abi_descriptors import slot_descriptors
from mindie_profiler.op_abi_padding import (
    synthesize_offsets, validate_group_list, validate_sequence_lengths,
)
from mindie_profiler.op_api_registry import (
    bind_captured_occurrence, call_mcp_tool, catalog_entry, catalog_operator,
    inspect_op_abi,
)
from mindie_profiler.repro_op import (
    _compact_occurrence, generate_single_op_reproducer,
)
from mindie_sim.diff_trace import attribute_diff
from mindie_sim.diff_trace_replay import replay

from nr_s6_support import (
    assert_plan_matches_signature, exec_script, fa_row, gmm_binding,
    paged_binding, paged_row, qli_row, spec_is_present,
)

# ------------------------------------------------------------------ helpers
def nd(shape, dtype="BF16", **extra):
    return {"shape": list(shape), "dtype": dtype, "layout": "ND", **extra}

def rms_norm_row(names=None, storage=None):
    extra = dict(storage or {})
    return {
        "op_type": "aclnnRmsNorm", "cann_version": "9.0",
        "input_shapes": [nd([4, 8], **extra), nd([8])],
        "input_names": names or ["x", "gamma"],
        "input_dtypes": ["BF16", "BF16"], "input_formats": ["ND", "ND"],
        "output_shapes": [nd([4, 8]), nd([4])], "output_names": ["y", "rstd"],
        "output_dtypes": ["BF16", "FP32"], "output_formats": ["ND", "ND"],
        "attrs": {"epsilon": 1e-6},
    }

def add_rms_norm_row():
    return {
        "op_type": "aclnnAddRmsNorm", "cann_version": "9.0",
        "input_shapes": [nd([4, 8]), nd([4, 8]), nd([8])],
        "input_names": ["x1", "x2", "gamma"],
        "input_dtypes": ["BF16", "BF16", "BF16"],
        "input_formats": ["ND", "ND", "ND"],
        "output_shapes": [nd([4, 8]), nd([4]), nd([4, 8])],
        "output_names": ["y", "rstd", "x_out"],
        "output_dtypes": ["BF16", "FP32", "BF16"],
        "output_formats": ["ND", "ND", "ND"],
        "attrs": {"epsilon": 1e-6},
    }

def swiglu_row(shape):
    return {
        "op_type": "aclnnSwiGlu", "cann_version": "9.0",
        "input_shapes": [nd(shape)], "input_names": ["x"],
        "output_shapes": [nd([shape[0], shape[-1] // 2])], "output_names": ["y"],
        "attrs": {"dim": -1},
    }

def moe_gating_row(k=2, out_k=None):
    out_k = out_k if out_k is not None else k
    return {
        "op_type": "MoeGatingTopKSoftmax", "cann_version": "9.0",
        "input_shapes": [nd([4, 8])], "input_names": ["x"],
        "output_shapes": [nd([4, out_k]), nd([4, out_k], "INT32"),
                          nd([4, out_k], "FP32")],
        "output_names": ["y", "expert_idx", "out"],
        "attrs": {"k": k},
    }

def chunk_row(lengths=(10, 20), total=30):
    return {
        "op_type": "ChunkGatedDeltaRule", "cann_version": "9.0",
        "input_shapes": [nd([total, 1, 128]), nd([total, 1, 128]),
                         nd([total, 1, 128]), nd([total, 1]), nd([total, 1]),
                         nd([1, 1, 128, 128]),
                         {"shape": [len(lengths)], "dtype": "INT32",
                          "layout": "ND", "values": list(lengths)}],
        "input_names": ["q", "k", "v", "beta", "g", "initial_state",
                        "actual_seq_lengths"],
        "output_shapes": [nd([total, 1, 128]), nd([1, 1, 128, 128])],
        "output_names": ["o", "final_state"],
        "attrs": {"scale": 0.088},
    }

def fia_row(kv_lengths=(16,)):
    return {
        "op_type": "aclnnFusedInferAttentionScoreV2", "cann_version": "9.0",
        "input_shapes": [nd([16, 8, 128]), nd([16, 128]), nd([16, 128])],
        "input_names": ["query", "key", "value"],
        "output_shapes": [nd([16, 8, 128])], "output_names": ["attention_out"],
        "attrs": {"input_layout": "TND", "num_heads": 8,
                  "num_key_value_heads": 8, "scale_value": 0.088,
                  "actual_seq_lengths": [16],
                  "actual_seq_lengths_kv": list(kv_lengths)},
    }

def rope_row():
    return {
        "op_type": "aclnnApplyRotaryPosEmbV2", "cann_version": "9.0",
        "input_shapes": [nd([1, 4, 8, 128])] * 4,
        "input_names": ["query_ref", "key_ref", "cos", "sin"],
        "attrs": {"layout": 4, "rotary_mode": 1},
    }

def moe_init_row():
    return {
        "op_type": "MoeInitRoutingV2", "cann_version": "9.0",
        "input_shapes": [nd([8, 16]), nd([8, 2], "INT32")],
        "input_names": ["x", "expert_idx"],
        "output_shapes": [nd([16, 16]), nd([16], "INT32"), nd([4], "INT32"),
                          nd([4], "INT32")],
        "output_names": ["expanded_x_out", "expanded_row_idx_out",
                         "expert_tokens_count_or_cumsum_out",
                         "expert_tokens_before_capacity_out"],
        "attrs": {"active_num": 16, "expert_num": 4, "drop_pad_mode": 0,
                  "expert_capacity": 16,
                  "expert_tokens_count_or_cumsum_flag": 1,
                  "expert_tokens_before_capacity_flag": True},
    }

def dynamic_quant_row():
    return {
        "op_type": "aclnnDynamicQuant", "cann_version": "9.0",
        "input_shapes": [nd([4, 8]), nd([4, 8])],
        "input_names": ["x", "smooth_scales"],
        "output_shapes": [nd([4, 8], "INT8"), nd([4, 8], "FP32")],
        "output_names": ["y", "scale"], "attrs": {"dst_type": 1},
    }

def _ready_bindings():
    return {
        "aclnnFlashAttentionVarLenScore": bind_captured_occurrence(fa_row()),
        "aclnnFusedInferAttentionScoreV2": bind_captured_occurrence(fia_row()),
        "aclnnApplyRotaryPosEmbV2": bind_captured_occurrence(rope_row()),
        "aclnnGroupedMatmulV4": gmm_binding(),
        "aclnnPagedAttention": paged_binding(),
        "aclnnDynamicQuant": bind_captured_occurrence(dynamic_quant_row()),
        "MoeInitRoutingV2": bind_captured_occurrence(moe_init_row()),
        "aclnnSwiGlu": bind_captured_occurrence(swiglu_row([2, 4])),
        "MoeGatingTopKSoftmax": bind_captured_occurrence(moe_gating_row()),
        "QuantLightningIndexer": bind_captured_occurrence(qli_row()),
        "aclnnRmsNorm": bind_captured_occurrence(rms_norm_row()),
        "aclnnAddRmsNorm": bind_captured_occurrence(add_rms_norm_row()),
        "ChunkGatedDeltaRule": bind_captured_occurrence(chunk_row()),
    }

# --------------------------------------------------------------------- R1
def test_r1_identical_trace_replays_to_identical_makespan():
    trace = {"total_ms": 7, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 2},
        {"name": "B", "stream": 0, "start_ms": 5, "duration_ms": 2}]}
    result = attribute_diff(trace, trace, launch_overhead_us=0)
    assert result["stages"] == {"R0": 7.0, "R1": 7.0, "R2": 7.0,
                                "R3": 7.0, "R4_model": 7.0, "O": 7.0}
    assert all(value == 0.0 for value in result["buckets"].values())
    assert result["attribution"]["graph_delta_ms"] == 0.0
    assert result["attribution"]["sched_delta_ms"] == 0.0
    assert result["attribution"]["op_delta_ms"] == 0.0
    assert result["attribution"]["comm_delta_ms"] == 0.0
    assert result["attribution"]["residual_ms"] == 0.0
    assert result["conservation"]["exact"] is True
    assert result["reconciliation"]["reconciled"] is True
    assert result["status"] == "reconciled"

def test_r1_serial_growth_is_op_delta_not_graph_or_schedule():
    predicted = {"total_ms": 4, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 2},
        {"name": "B", "stream": 0, "start_ms": 2, "duration_ms": 2,
         "deps": [0]}]}
    captured = {"total_ms": 5, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 3},
        {"name": "B", "stream": 0, "start_ms": 3, "duration_ms": 2,
         "deps": [0]}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["attribution"]["op_delta_ms"] == pytest.approx(1.0)
    assert result["attribution"]["graph_delta_ms"] == 0.0
    assert result["attribution"]["sched_delta_ms"] == 0.0
    assert result["buckets"]["kernel_roofline_and_clock_delta_ms"] == pytest.approx(1.0)
    assert result["buckets"]["graph_lowering_delta_ms"] == 0.0

def test_r1_deps_index_never_crashes_and_stream_fifo_is_enforced():
    # Self/out-of-range deps are ignored; the two same-stream ops serialize.
    ops = [{"key": "a", "name": "A", "stream": 0, "start": 0, "duration": 2,
            "deps": [0, 99]},
           {"key": "b", "name": "B", "stream": 0, "start": 0, "duration": 3,
            "deps": []}]
    result = replay(ops, [2, 3], window=(0, 10), starts=[0, 0])
    assert result["cycle"] is False
    assert result["starts"] == [0.0, 2.0]
    assert result["ends"] == [2.0, 5.0]
    assert result["wall_ms"] == 5.0

def test_r1_stream_fifo_uses_enqueue_order_not_timestamps():
    ops = [{"key": "a", "name": "A", "stream": 0, "start": 10, "duration": 2,
            "deps": []},
           {"key": "b", "name": "B", "stream": 0, "start": 0, "duration": 2,
            "deps": []}]
    result = replay(ops, [2, 2], window=(0, 20), starts=[10, 0])
    assert result["starts"] == [10.0, 12.0]
    assert result["ends"] == [12.0, 14.0]

def test_r1_occurrence_matching_is_immutable_and_reports_unmatched():
    predicted = {"total_ms": 4, "ops": [
        {"name": "Matmul", "stream": 0, "start_ms": 0, "duration_ms": 2}]}
    captured = {"total_ms": 4, "ops": [
        {"name": "Matmul", "stream": 1, "start_ms": 0, "duration_ms": 2},
        {"name": "Matmul", "stream": 0, "start_ms": 2, "duration_ms": 2,
         "abi_sha256": "sha256:other"}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    codes = [issue["code"] for issue in result["issues"]]
    assert "unmatched_occurrences" in codes
    assert result["coverage"]["added_ops"] == 2
    assert result["coverage"]["removed_ops"] == 1
    assert result["status"] == "partial"

def test_r1_residual_gate_blocks_large_unexplained_time():
    predicted = {"total_ms": 10, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 10}]}
    captured = {"total_ms": 20, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 10}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["reconciliation"]["residual_ms"] == pytest.approx(10.0)
    assert result["reconciliation"]["reconciled"] is False
    assert result["status"] == "partial"
    assert any(issue["code"] == "unexplained_residual" for issue in result["issues"])
    assert result["buckets"]["unexplained_residual_delta_ms"] == pytest.approx(10.0)
    assert result["buckets"]["kernel_roofline_and_clock_delta_ms"] == 0.0
    assert sum(result["buckets"].values()) == pytest.approx(result["total_delta_ms"])

# --------------------------------------------------------------------- R2
def test_r2_release_list_membership_does_not_certify_a_build():
    match = catalog_operator("aclnnGroupedMatmulV4", cann_version="9.0")
    assert match["version_supported"] is True
    assert match["version_qualified"] is False
    assert match["qualification_state"] == "schema_pinned_unverified"
    card = inspect_op_abi("aclnnGroupedMatmulV4", cann_version="9.0")["card"]
    assert card["complete"] is False
    missing = inspect_op_abi("aclnnGroupedMatmulV4")["card"]
    assert missing["version_qualified"] is False
    assert missing["complete"] is False
    assert missing["qualification_state"] == "version_not_requested"

def test_r2_identity_covers_scalars_dtype_layout_and_storage():
    base = bind_captured_occurrence(fa_row())
    scaled = bind_captured_occurrence(fa_row(
        attrs={**fa_row()["attrs"], "scale": 0.25}))
    assert (base["identity"]["call_abi_sha256"]
            != scaled["identity"]["call_abi_sha256"])
    assert (base["identity"]["capture_shape_abi_sha256"]
            == scaled["identity"]["capture_shape_abi_sha256"])
    assert base["identity"]["capture_verified"] is False
    assert base["qualification"]["version_qualified"] is False

    storage = bind_captured_occurrence(rms_norm_row(
        storage={"strides": [1, 4], "storage_offset": 2,
                 "storage_bytes": 128, "storage_id": 7}))
    plain = bind_captured_occurrence(rms_norm_row())
    assert storage["status"] == plain["status"] == "bound"
    assert (storage["identity"]["call_abi_sha256"]
            != plain["identity"]["call_abi_sha256"])
    assert (storage["identity"]["capture_shape_abi_sha256"]
            == plain["identity"]["capture_shape_abi_sha256"])

    fp16_gamma = rms_norm_row()
    fp16_gamma["input_shapes"][1] = nd([8], "FP16")
    dtyped = bind_captured_occurrence(fp16_gamma)
    assert dtyped["status"] == plain["status"] == "bound"
    assert (dtyped["identity"]["call_abi_sha256"]
            != plain["identity"]["call_abi_sha256"])

def test_r2_capture_digest_is_raw_before_named_reordering():
    plain = bind_captured_occurrence(rms_norm_row())
    reordered = bind_captured_occurrence(rms_norm_row(names=["gamma", "x"]))
    assert plain["status"] == reordered["status"] == "bound"
    assert (plain["identity"]["capture_shape_abi_sha256"]
            == reordered["identity"]["capture_shape_abi_sha256"])
    assert (plain["identity"]["call_abi_sha256"]
            != reordered["identity"]["call_abi_sha256"])

# --------------------------------------------------------------------- R3
@pytest.mark.parametrize("name", sorted(_ready_bindings()))
def test_r3_ready_call_plans_bind_strict_signature_stubs(name):
    bindings = _ready_bindings()
    binding = bindings[name]
    assert binding["status"] == "bound", (name, binding["issues"])
    assert binding["repro_status"] == "ready"
    assert_plan_matches_signature(binding, catalog_entry(name)["repro_recipe"])

@pytest.mark.parametrize("name", sorted(_ready_bindings()))
def test_r3_every_ready_script_has_a_clean_dry_run(name):
    binding = _ready_bindings()[name]
    script = generate_single_op_reproducer(binding)["script"]
    namespace = exec_script(script)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = namespace["main"](["--dry-run"])
    assert code == 0, buffer.getvalue()
    payload = json.loads(buffer.getvalue())
    assert payload["status"] == "dry_run"
    assert payload["failed_checks"] == []
    assert payload["missing_attrs"] == []

def test_r3_fa_uses_pse_prefix_and_exact_names():
    binding = bind_captured_occurrence(fa_row())
    plan = _compact_occurrence(binding)["call_plan"]
    assert "pse" in plan["keyword"]
    assert "pse_shift" not in plan["keyword"]
    assert plan["keyword"]["pse"]["name"] == "real_shift"
    assert plan["keyword"]["prefix"]["kind"] == "array"
    assert plan["keyword"]["actual_seq_qlen"]["name"] == "actual_seq_q_len"
    assert catalog_entry("aclnnFlashAttentionVarLenScore")["repro_recipe"][
        "signature"]["returns"]["count"] == 7

def test_r3_fia_uses_tensor_key_value_and_dequant_names():
    binding = bind_captured_occurrence(fia_row())
    plan = _compact_occurrence(binding)["call_plan"]
    assert "dequant_scale1" in plan["keyword"]
    assert "deq_scale1" not in plan["keyword"]
    assert "deq_scale2" not in plan["keyword"]
    assert all(spec["kind"] == "tensor"
               for spec in plan["positional"] if spec["name"] in {"key", "value"})

def test_r3_rope_layout_and_mode_enums_are_converted():
    binding = bind_captured_occurrence(rope_row())
    plan = _compact_occurrence(binding)["call_plan"]
    assert plan["keyword"]["layout"]["value"] == "TND"
    assert plan["keyword"]["rotary_mode"]["value"] == "half"
    script = generate_single_op_reproducer(binding)["script"]
    namespace = {"__name__": "signature_probe"}
    exec(compile(script, "<generated>", "exec"), namespace)
    seen = {}
    namespace["_resolve"] = lambda _path: (
        lambda *args, **kwargs: seen.update(kwargs))
    namespace["_invoke"](plan, {}, {}, {}, {"layout": 4,
                                            "rotary_mode": "half"}, {})
    assert seen["layout"] == "TND"
    assert seen["rotary_mode"] == "half"
    broken = {**rope_row(), "attrs": {"layout": 99, "rotary_mode": 1}}
    with pytest.raises(ProfilerUsageError):
        _compact_occurrence(bind_captured_occurrence(broken))

def test_r3_absent_optional_scalars_are_omitted_not_passed_none():
    attrs = {key: value for key, value in fa_row()["attrs"].items()
             if key not in {"pre_tokens", "next_tokens", "inner_precise",
                            "sparse_mode"}}
    binding = bind_captured_occurrence(fa_row(attrs=attrs))
    assert binding["status"] == "bound"
    plan = _compact_occurrence(binding)["call_plan"]
    script = generate_single_op_reproducer(binding)["script"]
    namespace = {"__name__": "signature_probe"}
    exec(compile(script, "<generated>", "exec"), namespace)
    seen = {}
    namespace["_resolve"] = lambda _path: (
        lambda *args, **kwargs: seen.update(kwargs))
    namespace["_invoke"](plan, {}, {}, {}, binding["attrs"], {})
    assert "pre_tokens" not in seen
    assert "next_tokens" not in seen
    assert seen["head_num"] == 8

def test_r3_gmm_list_arguments_are_exact_and_activation_lists_preserved():
    recipe = catalog_entry("aclnnGroupedMatmulV4")["repro_recipe"]
    for name in ("activation_input", "activation_quant_scale",
                 "activation_quant_offset"):
        assert name in recipe["keyword"]
        assert recipe["keyword"][name]["optional"] is True
    plan = _compact_occurrence(gmm_binding())["call_plan"]
    assert plan["keyword"]["x"]["kind"] == "tensor_list"
    assert plan["keyword"]["weight"]["kind"] == "tensor_list"
    # Exact declared lengths are respected; a surplus descriptor is not appended.
    surplus = bind_captured_occurrence({
        "op_type": "aclnnGroupedMatmulV4", "cann_version": "9.0",
        "input_shapes": ["[64,128]", "[4,128,64]", "[4]", "[64,64]"],
        "input_dtypes": ["BF16", "BF16", "INT64", "BF16"],
        "input_formats": ["ND"] * 4,
        "input_tensor_list_lengths": {"x": 1, "weight": 1},
        "attrs": {"group_list_type": 0, "group_type": 0, "split_item": 0,
                  "act_type": 0},
        "output_shapes": ["[64,64]"], "output_dtypes": ["BF16"],
        "output_formats": ["ND"]})
    assert surplus["status"] == "abi_mismatch"
    assert surplus["conservation"]["exact"] is False
    assert [len(record.get("items") or ()) for record in surplus["inputs"]
            if record["name"] in {"x", "weight"}] == [1, 1]
    assert surplus["conservation"]["surplus_input_slots"][0]["position"] == 3

def test_r3_moe_routing_dynamic_quant_and_blocked_signature_metadata():
    routing = _compact_occurrence(bind_captured_occurrence(moe_init_row()))
    keyword = routing["call_plan"]["keyword"]
    assert keyword["expert_tokens_num_type"]["value"] == 1
    assert keyword["expert_tokens_num_flag"]["value"] is True
    quant = _compact_occurrence(bind_captured_occurrence(dynamic_quant_row()))
    assert quant["call_plan"]["keyword"]["dst_type"]["value"] == 1
    for name in ("aclnnAddRmsNormDynamicQuant", "CausalConv1d",
                 "FusedRecurrentGatedDeltaRule", "MlaPrologV2"):
        recipe = catalog_entry(name)["repro_recipe"]
        assert recipe["status"] == "blocked"
        assert recipe["repro_supported"] is False
        assert recipe["signature"]["verified"] is False
    assert "beta" in catalog_entry("aclnnAddRmsNormDynamicQuant")[
        "repro_recipe"]["keyword"]
    assert catalog_entry("aclnnAddRmsNormDynamicQuant")["repro_recipe"][
        "signature"]["returns"]["count"] == 5
    assert "activation" in catalog_entry("CausalConv1d")["repro_recipe"]["keyword"]
    assert "pad_slot_id" in catalog_entry("CausalConv1d")["repro_recipe"]["keyword"]
    assert "scale" in catalog_entry("FusedRecurrentGatedDeltaRule")[
        "repro_recipe"]["keyword"]
    assert "inplace_final_state" in catalog_entry(
        "FusedRecurrentGatedDeltaRule")["repro_recipe"]["keyword"]
    assert any("WeightNz" in note for note in catalog_entry("MlaPrologV2")[
        "repro_recipe"]["notes"])
    swiglu = catalog_entry("GroupedMatmulSwigluQuant")["repro_recipe"]
    assert swiglu["keyword"]["bias"]["optional"] is True
    assert swiglu["keyword"]["offset"]["optional"] is True

def test_r3_external_unpinned_entries_are_blocked_not_ready():
    binding = bind_captured_occurrence({
        "op_type": "aclnnMatmul", "cann_version": "9.2",
        "input_shapes": ["[2,2]", "[2,2]"], "input_dtypes": ["BF16", "BF16"],
        "input_formats": ["ND", "ND"], "output_shapes": ["[2,2]"],
        "output_dtypes": ["BF16"], "output_formats": ["ND"],
        "attrs": {"cube_math_type": 0}})
    assert binding["status"] == "blocked"
    assert binding["slot_status"] == "blocked"
    assert binding["repro_status"] == "blocked"
    assert binding["repro_supported"] is False
    assert binding["identity"] is None

def test_r3_executable_preconditions_fail_closed():
    odd = bind_captured_occurrence(swiglu_row([2, 3]))
    assert odd["status"] == "bound"
    with pytest.raises(ProfilerUsageError) as excinfo:
        _compact_occurrence(odd)
    assert "invalid_precondition" in str(excinfo.value)
    assert "odd" in str(excinfo.value)

    qli = bind_captured_occurrence(qli_row(
        input_dtypes=["BF16"] + qli_row()["input_dtypes"][1:]))
    with pytest.raises(ProfilerUsageError):
        _compact_occurrence(qli)
    qli_rank = bind_captured_occurrence(qli_row(
        output_shapes=["[48,4]"], output_dtypes=["INT32"], output_formats=["ND"]))
    with pytest.raises(ProfilerUsageError):
        _compact_occurrence(qli_rank)
    qli_dtype = bind_captured_occurrence(qli_row(
        output_dtypes=["BF16"]))
    with pytest.raises(ProfilerUsageError):
        _compact_occurrence(qli_dtype)

    topk = bind_captured_occurrence(moe_gating_row(k=9, out_k=9))
    with pytest.raises(ProfilerUsageError) as excinfo:
        _compact_occurrence(topk)
    assert "k=9" in str(excinfo.value)
    with pytest.raises(ProfilerUsageError):
        _compact_occurrence(bind_captured_occurrence(moe_gating_row(k=0, out_k=0)))
    with pytest.raises(ProfilerUsageError):
        _compact_occurrence(bind_captured_occurrence(
            moe_gating_row(k=2, out_k=3)))

# ---------------------------------------------------------------- R4 / R5
def test_r4_mapping_columns_are_preserved_and_mismatch_blocks():
    parsed = slot_descriptors({
        "input_shapes": [{"shape": [4, 8]}, {"shape": [4]}],
        "input_dtypes": ["BF16"], "input_formats": ["ND", "ND"]}, "input")
    codes = {issue["code"] for issue in parsed["issues"]}
    assert "descriptor_column_mismatch" in codes
    assert parsed["slots"][0]["dtype"] == "bf16"
    assert parsed["slots"][0]["dtype_column"] == "BF16"
    assert "layout_column" in parsed["slots"][1]

def test_r5_mapping_present_and_shape_present_flags_are_respected():
    present_false = slot_descriptors({
        "input_shapes": [nd([4, 8]),
                         {"shape": [4], "dtype": "BF16", "layout": "ND",
                          "present": False}]}, "input")
    assert present_false["slots"][1]["state"] == "absent"
    assert present_false["slots"][1]["present"] is False
    shape_false = slot_descriptors({
        "input_shapes": [nd([4, 8]),
                         {"shape": [4], "shape_present": False,
                          "dtype": "BF16", "layout": "ND"}]}, "input")
    assert shape_false["slots"][1]["state"] == "missing"
    assert shape_false["slots"][1]["shape"] is None

def test_r5_scalar_attributes_are_type_and_range_checked():
    garbage = bind_captured_occurrence(fa_row(
        attrs={**fa_row()["attrs"], "num_heads": "garbage"}))
    codes = [issue["code"] for issue in garbage["issues"]]
    assert "invalid_attribute_type" in codes
    assert garbage["status"] != "bound"
    ranged = bind_captured_occurrence(fa_row(
        attrs={**fa_row()["attrs"], "num_heads": 0}))
    assert any(issue["code"] == "invalid_attribute_range"
               for issue in ranged["issues"])
    assert ranged["status"] != "bound"

def test_r5_undefined_means_null_policy_is_required_and_honored():
    entry = json.loads(json.dumps(catalog_entry("MoeGatingTopKSoftmax")))
    for spec in entry["c_abi_slots"]["slot_specs"]["inputs"]:
        if spec["name"] == "finished":
            spec.pop("undefined_means_null", None)
    match = {"name": "MoeGatingTopKSoftmax", "entry": entry,
             "version_supported": True, "abi_id_supported": True,
             "versions": entry["cann_versions"], "match": "exact",
             "qualification_state": "schema_pinned_unverified",
             "version_qualified": False, "capture_verified": False,
             "schema_pinned": True, "release_basis": entry["release_basis"]}
    row = {"op_type": "MoeGatingTopKSoftmax", "cann_version": "9.0",
           "input_shapes": ["[4,8]", ""], "input_dtypes": ["BF16", ""],
           "input_formats": ["ND", ""],
           "output_shapes": ["[4,2]"] * 3, "output_dtypes": ["BF16"] * 3,
           "output_formats": ["ND"] * 3, "attrs": {"k": 2}}
    binding = bind_resolved_occurrence(row, match)
    assert "undefined_policy_unspecified" in [
        issue["code"] for issue in binding["issues"]]
    # Explicit policy false turns an undefined optional slot into a hard error.
    for spec in entry["c_abi_slots"]["slot_specs"]["inputs"]:
        if spec["name"] == "finished":
            spec["undefined_means_null"] = False
    denied = bind_resolved_occurrence(row, match)
    assert "undefined_not_nullable" in [issue["code"] for issue in denied["issues"]]

# --------------------------------------------------------------------- R6
def test_r6_sequence_validators_reject_negative_decreasing_and_oversized():
    assert validate_sequence_lengths([-1, 33], encoding="cumsum",
                                     extent=48)["valid"] is False
    decreasing = validate_sequence_lengths([32, 30, 73], encoding="cumsum",
                                           extent=128)
    assert decreasing["valid"] is False
    assert {item["code"] for item in decreasing["violations"]} >= {
        "sequence_not_monotone"}
    assert validate_sequence_lengths([999999], encoding="cumsum",
                                     extent=48)["valid"] is False
    assert validate_sequence_lengths([0, 10, 30], encoding="cumsum",
                                     extent=30, leading_zero=True)["valid"] is True

@pytest.mark.parametrize("q,kv", [([-1, 33], [33]), ([32, 30, 73], [73]),
                                  ([999999], [999999])])
def test_r6_invalid_fa_lengths_block_binding(q, kv):
    binding = bind_captured_occurrence(fa_row(
        attrs={**fa_row()["attrs"], "actual_seq_q_len": q,
               "actual_seq_kv_len": kv}))
    assert binding["status"] != "bound"
    assert binding["padding"]["valid"] is False
    assert binding["padding"]["charged_tokens"] == 0

def test_r6_invalid_q_end_is_rejected_even_with_effective_zero():
    binding = bind_captured_occurrence(fa_row(
        attrs={**fa_row()["attrs"], "actual_seq_q_len": [-1],
               "effective_tokens": 0}))
    assert binding["status"] != "bound"
    assert "sequence_q_negative" in [
        item["code"] for item in binding["padding"]["violations"]]

def test_r6_chunk_lengths_are_not_interpreted_as_cumulative():
    binding = bind_captured_occurrence(chunk_row(lengths=(10, 20), total=30))
    assert binding["status"] == "bound"
    assert binding["padding"]["logical_tokens"] == 30
    assert binding["padding"]["effective_tokens"] == 30
    assert binding["padding"]["qualification"]["encoding"] == "lengths"
    assert synthesize_offsets([10, 20], cumulative=True,
                              leading_zero=True) == [0, 10, 30]
    assert synthesize_offsets([10, 20], cumulative=False) == [10, 20]

def test_r6_fractional_group_counts_are_rejected_not_rounded():
    checked = validate_group_list([1.5, 2], 1, 8)
    assert checked["valid"] is False
    assert any(item["code"] == "group_list_fractional"
               for item in checked["violations"])
    with pytest.raises(ValueError):
        from mindie_profiler.op_abi_padding import synthesize_group_list
        synthesize_group_list(8, 1.5, 0)

def test_r6_sim_fails_closed_when_group_validation_fails():
    predicted = {"total_ms": 10, "ops": [
        {"name": "X", "stream": 0, "start_ms": 0, "duration_ms": 10}]}
    captured = json.loads(json.dumps(predicted))
    result = attribute_diff(predicted, captured, cann_version="9.0", padding={
        "aclnnGroupedMatmulV4": {"bucket_tokens": 128,
                                 "bound_args": {"group_list": [32, 30, 73]}}})
    assert result["status"] == "partial"
    assert result["padding"]["valid"] is False
    assert result["padding"]["charges"][0]["charged_tokens"] == 0
    assert any(issue["code"] == "padding_validation_failed"
               for issue in result["issues"])

# ---------------------------------------------------------------- R7 / R8
def _paged_values(table_values=None, context_values=None, table_shape=(16, 16)):
    row = paged_row(input_names=["query", "key_cache", "value_cache",
                                 "block_table", "context_lens"])
    table = {"shape": list(table_shape), "dtype": "INT32", "layout": "ND"}
    if table_values is not None:
        table["values"] = table_values
    context = {"shape": [16], "dtype": "INT32", "layout": "ND"}
    if context_values is not None:
        context["values"] = context_values
    row["input_shapes"] = [nd([16, 8, 128]), nd([256, 16, 8, 128]),
                           nd([256, 16, 8, 128]), table, context]
    return row

def test_r7_captured_page_ids_are_checked_after_substitution():
    row = _paged_values(table_values=[[9999] * 16 for _ in range(16)])
    binding = bind_captured_occurrence(row)
    assert binding["status"] == "bound"
    occurrence = _compact_occurrence(binding)
    assert occurrence["status"] == "blocked"
    assert occurrence["checks"]["block_table_in_bounds"] is False
    assert occurrence["checks"]["metadata_installable"] is False
    with pytest.raises(ProfilerUsageError):
        generate_single_op_reproducer(binding)

def test_r7_captured_context_must_fit_the_block_table_width():
    row = _paged_values(table_shape=(16, 8),
                        context_values=[2048] + [0] * 15)
    binding = bind_captured_occurrence(row)
    blocked = _compact_occurrence(binding)
    assert blocked["status"] == "blocked"
    assert blocked["checks"]["context_fits_block_table"] is False
    with pytest.raises(ProfilerUsageError):
        generate_single_op_reproducer(binding)
    occurrence = _compact_occurrence(paged_binding())
    assert occurrence["checks"]["metadata_installable"] is True

def test_r8_metadata_only_capture_is_labelled_honestly():
    row = _paged_values(context_values=[128] * 16)
    occurrence = _compact_occurrence(bind_captured_occurrence(row))
    assert occurrence["fidelity"] == "metadata_captured_activations_synthetic"
    assert occurrence["metadata"]["fidelity"] == (
        "metadata_captured_activations_synthetic")
    plain = _compact_occurrence(paged_binding())
    assert plain["fidelity"] == "descriptor_synthetic"

def test_r8_storage_and_present_fields_survive_into_allocate():
    row = rms_norm_row(storage={"strides": [1, 4], "storage_offset": 2, "storage_bytes": 128, "storage_id": 7})
    binding = bind_captured_occurrence(row)
    occurrence = _compact_occurrence(binding)
    x_spec = next(spec for spec in occurrence["allocations"] if spec["name"] == "x")
    assert x_spec["storage"] == {"strides": [1, 4], "storage_offset": 2, "storage_bytes": 128, "storage_id": 7}
    assert x_spec["present"] is True
    assert "cannot be reproduced" in " ".join( generate_single_op_reproducer(binding)["manifest"]["limitations"])

def test_r8_captured_non_metadata_values_are_honored():
    row = rms_norm_row()
    row["input_shapes"][0] = nd([4, 8], values=[0.5] * 32)
    binding = bind_captured_occurrence(row)
    occurrence = _compact_occurrence(binding)
    x_spec = next(spec for spec in occurrence["allocations"] if spec["name"] == "x")
    assert x_spec["values"] == [0.5] * 32
    assert occurrence["fidelity"] == "shape_and_values_captured"
    all_values = rms_norm_row()
    all_values["input_shapes"][0] = nd([4, 8], values=[0.5] * 32)
    all_values["input_shapes"][1] = nd([8], values=[1.0] * 8)
    full = _compact_occurrence(bind_captured_occurrence(all_values))
    assert full["fidelity"] == "value_captured"

def test_r8_manifest_and_dry_run_are_backed_by_real_checks(tmp_path):
    result = generate_single_op_reproducer(paged_binding(), output_dir=tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["fidelity"] == result["fidelity"]
    assert manifest["checks"]["metadata_installable"] is True
    assert checked_io.path_exists(Path(tmp_path) / "repro.py")
