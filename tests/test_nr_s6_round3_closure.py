"""Round-3 closure: direct regressions for every R1..R14 counterexample.

[Role]
  Reproduce each executed counterexample from ``astra_review_r3.md`` against the
  fixed contracts: symmetric follower shift, per-(rank, stream) FIFO, honest
  identity/version qualification, typed callable arguments, span deficits,
  tensor-list element state, physical sequence/page bounds, strict value numel,
  shared probe failure reduction, live warmup/deadline behavior, affirmative
  calibration evidence, per-sweep L2 evidence, UID/raw-index round-trips and
  complete-envelope token budgets.

[Invariants]
  * Probe tests use a peer-reduction stub that records the exact shared decision
    sequence for each simulated rank.
  * The deadline test starts from an admitted plan and advances the monotonic
    clock during allocation; it does not use an already rejected plan.
  * Callable tests execute the generated ``_invoke`` against a typed schema stub,
    not a name-only signature.
  * Artifact tests verify that two invocations with different iteration counts
    use different directories and never overwrite each other.

[Timeouts & Locks]
  Pure in-process stubs; no NPU, SSH or distributed process is started.

[Side-Effect Policy]
  Writes only under pytest's ``tmp_path`` or content-addressed process temp
  directories created by the reproducer; no reference tree is modified.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import types

import pytest

from mindie_profiler.fabric_probe import build_fabric_probe_plan
from mindie_profiler.fabric_probe_fit import fit_calibrated_fabric_profile
from mindie_profiler.op_api_registry import (
    bind_captured_occurrence, call_mcp_tool as registry_mcp,
    catalog_entry, inspect_op_abi,
)
from mindie_profiler.repro_op import (
    _compact_occurrence, _row_from_args, _slot_allocations, call_mcp_tool,
    extract_raw_rows, generate_single_op_reproducer,
)
from mindie_profiler.repro_preconditions import (
    SUPPORTED_PRECONDITION_KINDS, precondition_problems,
)
from mindie_profiler.token_budget import bounded_envelope, estimate_tokens
from mindie_sim.diff_trace import attribute_diff, effective_operator_rows
from mindie_sim.diff_trace_replay import _op_uid

from nr_s6_support import exec_script, fa_binding, fa_row, paged_binding, paged_row
from nr_s6_round3_probe import _Tensor, _probe_run

ROOT = Path(__file__).parents[1]


# ------------------------------------------------------------------- helpers
def _nd(shape, dtype="BF16", **extra):
    return {"shape": list(shape), "dtype": dtype, "layout": "ND", **extra}


def _rms_row(x_values=None):
    row = {
        "op_type": "aclnnRmsNorm", "cann_version": "9.0",
        "input_shapes": [_nd([4, 8]), _nd([8])], "input_names": ["x", "gamma"],
        "input_dtypes": ["BF16", "BF16"], "input_formats": ["ND", "ND"],
        "output_shapes": [_nd([4, 8]), _nd([4])], "output_names": ["y", "rstd"],
        "output_dtypes": ["BF16", "FP32"], "output_formats": ["ND", "ND"],
        "attrs": {"epsilon": 1e-6},
    }
    if x_values is not None:
        row["input_shapes"][0] = _nd([4, 8], values=x_values)
    return row


def _dynamic_quant_row(**attrs):
    return {
        "op_type": "aclnnDynamicQuant", "cann_version": "9.0",
        "input_shapes": [_nd([4, 8]), _nd([4, 8])],
        "input_names": ["x", "smooth_scales"],
        "input_dtypes": ["BF16"] * 2, "input_formats": ["ND"] * 2,
        "output_shapes": [_nd([4, 8], "INT8"), _nd([4, 8], "FP32")],
        "output_names": ["y", "scale"], "output_dtypes": ["INT8", "FP32"],
        "output_formats": ["ND"] * 2,
        "attrs": {"dst_type": 1, **attrs},
    }


def _moe_row(expert_values=None):
    idx = _nd([8, 2], "INT32")
    if expert_values is not None:
        idx["values"] = expert_values
    return {
        "op_type": "MoeInitRoutingV2", "cann_version": "9.0",
        "input_shapes": [_nd([8, 16]), idx], "input_names": ["x", "expert_idx"],
        "input_dtypes": ["BF16", "INT32"], "input_formats": ["ND", "ND"],
        "output_shapes": [_nd([16, 16]), _nd([16], "INT32"),
                          _nd([4], "INT32"), _nd([4], "INT32")],
        "output_names": ["expanded_x_out", "expanded_row_idx_out",
                         "expert_tokens_count_or_cumsum_out",
                         "expert_tokens_before_capacity_out"],
        "output_dtypes": ["BF16", "INT32", "INT32", "INT32"],
        "output_formats": ["ND"] * 4,
        "attrs": {"active_num": 16, "expert_num": 4, "drop_pad_mode": 0,
                  "expert_capacity": 16, "expert_tokens_count_or_cumsum_flag": 1,
                  "expert_tokens_before_capacity_flag": True},
    }


def _gmm_row(x_slot=None, out_lengths=None):
    x_slot = x_slot or _nd([64, 128])
    row = {
        "op_type": "aclnnGroupedMatmulV4", "cann_version": "9.0",
        "input_shapes": [x_slot, _nd([4, 128, 64], "BF16"),
                         _nd([4], "INT64")],
        "input_names": ["x", "weight", "group_list"],
        "input_dtypes": ["BF16", "BF16", "INT64"],
        "input_formats": ["ND", "FRACTAL_NZ", "ND"],
        "input_tensor_list_lengths": {"x": 1, "weight": 1},
        "output_shapes": [_nd([64, 64])], "output_names": ["out"],
        "output_dtypes": ["BF16"], "output_formats": ["ND"],
        "attrs": {"group_list_type": 0, "group_type": 0, "act_type": 0,
                  "split_item": 0, "group_list": [16, 32, 48, 64]},
    }
    if x_slot.get("layout") != "ND":
        row["input_formats"][0] = x_slot["layout"]
    if out_lengths is not None:
        row["output_tensor_list_lengths"] = {"out": out_lengths}
    return row


def _paged_row(table_values=None, page_capacity=256):
    table = _nd([16, 16], "INT32")
    if table_values is not None:
        table["values"] = table_values
    row = paged_row(input_names=["query", "key_cache", "value_cache",
                                 "block_table", "context_lens"])
    row["input_shapes"] = [_nd([16, 8, 128]), _nd([page_capacity, 16, 8, 128]),
                           _nd([page_capacity, 16, 8, 128]), table, _nd([16], "INT32")]
    return row


def _bsh_fa_row(lengths):
    return fa_row(
        input_shapes=["[2,4,1024]"] * 7, input_dtypes=["BF16"] * 7,
        attrs={**fa_row()["attrs"], "input_layout": "BSH",
               "actual_seq_q_len": lengths, "actual_seq_kv_len": lengths},
        output_shapes=["[2,4,1024]"] + ["[2,4,8]"] * 3,
        output_dtypes=["BF16"] * 4)


# --------------------------------------------------------------------- R1
def test_r1_symmetric_follower_moves_earlier_without_a_floor():
    predicted = {"total_ms": 4, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 2},
        {"name": "B", "stream": 0, "start_ms": 2, "duration_ms": 2,
         "deps": [0]}]}
    captured = {"total_ms": 3, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 1},
        {"name": "B", "stream": 0, "start_ms": 1, "duration_ms": 2,
         "deps": [0]}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["stages"] == {"R0": 4.0, "R1": 4.0, "R2": 4.0, "R3": 4.0,
                                "R4_model": 3.0, "O": 3.0}
    assert result["attribution"]["op_delta_ms"] == pytest.approx(-1.0)
    assert result["attribution"]["residual_ms"] == 0.0
    assert result["buckets"]["kernel_roofline_and_clock_delta_ms"] == pytest.approx(-1.0)
    assert result["reconciliation"]["reconciled"] is True


def test_r1_explicit_host_gap_pins_the_captured_start():
    predicted = {"total_ms": 3.5, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 1.5},
        {"name": "B", "stream": 0, "start_ms": 1.5, "duration_ms": 2,
         "deps": [0]}]}
    captured = {"total_ms": 4, "gaps": [{"stream": 0, "start_ms": 1,
                                         "duration_ms": 1}],
                "ops": [{"name": "A", "stream": 0, "start_ms": 0,
                         "duration_ms": 1},
                        {"name": "B", "stream": 0, "start_ms": 2,
                         "duration_ms": 2, "deps": [0]}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    assert result["stages"]["R4_model"] == pytest.approx(4.0)
    assert result["stages"]["O"] == 4.0
    assert result["reconciliation"]["reconciled"] is True


def test_r1_fifo_is_keyed_by_rank_and_stream():
    trace = {"total_ms": 2, "ops": [
        {"name": "A", "rank": 0, "stream": 0, "start_ms": 0, "duration_ms": 2},
        {"name": "A", "rank": 1, "stream": 0, "start_ms": 0, "duration_ms": 2}]}
    result = attribute_diff(trace, trace, launch_overhead_us=0)
    assert result["stages"] == {"R0": 2.0, "R1": 2.0, "R2": 2.0, "R3": 2.0,
                                "R4_model": 2.0, "O": 2.0}
    assert result["total_delta_ms"] == 0.0
    assert result["reconciliation"]["reconciled"] is True


# --------------------------------------------------------------------- R2
def test_r2_identity_is_not_complete_without_build_or_capture_qualification():
    binding = fa_binding()
    identity = binding["identity"]
    assert binding["status"] == "bound"
    assert binding["repro_status"] == "ready"
    assert identity["status"] == "schema_bound"
    assert identity["complete"] is False
    assert identity["version_qualified"] is False
    assert identity["capture_verified"] is False
    assert binding["qualification"]["version_qualified"] is False


def test_r2_forwarded_attrs_are_validated_and_hashed():
    token = bind_captured_occurrence(_dynamic_quant_row(quant_mode="per_token"))
    channel = bind_captured_occurrence(_dynamic_quant_row(quant_mode="per_channel"))
    assert token["status"] == channel["status"] == "bound"
    assert (token["identity"]["call_abi_sha256"]
            != channel["identity"]["call_abi_sha256"])
    invalid = bind_captured_occurrence(_dynamic_quant_row(quant_mode=7))
    assert invalid["status"] != "bound"
    assert "invalid_attribute_type" in [issue["code"] for issue in invalid["issues"]]
    charge = effective_operator_rows("aclnnGroupedMatmulV4", 64, None,
                                     {"group_list": [16, 32, 48, 64]},
                                     cann_version="9.0")
    assert charge["version_supported"] is True
    assert charge["version_qualified"] is False
    assert charge["version_verified"] is False


# --------------------------------------------------------------------- R3
def test_r3_integer_quant_mode_is_rejected_before_ready():
    binding = bind_captured_occurrence(_dynamic_quant_row(quant_mode=7))
    with pytest.raises(Exception) as excinfo:
        _compact_occurrence(binding)
    assert "invalid_attribute_type" in str(excinfo.value)
    # Defeat the binding gate deliberately: the call plan must still reject.
    valid = bind_captured_occurrence(_dynamic_quant_row(quant_mode="per_token"))
    tampered = copy.deepcopy(valid)
    tampered["attrs"]["quant_mode"] = 7
    for record in tampered["attr_slots"]:
        if record["name"] == "quant_mode":
            record["value"] = 7
    with pytest.raises(Exception) as excinfo:
        _compact_occurrence(tampered)
    assert "quant_mode" in str(excinfo.value)


def _typed_dynamic_quant_stub():
    signature = catalog_entry("aclnnDynamicQuant")["repro_recipe"]["signature"]
    kinds = {name: spec["kind"] for name, spec in signature["params"].items()}

    def stub(*_args, **kwargs):
        for name, value in kwargs.items():
            if value is None:
                continue
            kind = kinds.get(name)
            if kind == "tensor":
                assert isinstance(value, _Tensor), (name, type(value))
            elif kind == "int":
                assert isinstance(value, int) and not isinstance(value, bool), (
                    f"{name} must be int, got {type(value).__name__}")
            elif kind == "str":
                assert isinstance(value, str), (
                    f"{name} must be str, got {type(value).__name__}")
            elif kind == "float":
                assert isinstance(value, (int, float)) and not isinstance(value, bool)
            elif kind == "bool":
                assert isinstance(value, bool)
        return ("y", "scale")
    return stub


def test_r3_generated_invoke_binds_a_typed_schema_stub():
    binding = bind_captured_occurrence(_dynamic_quant_row(quant_mode="per_token"))
    occurrence = _compact_occurrence(binding)
    script = generate_single_op_reproducer(binding)["script"]
    namespace = exec_script(script)
    namespace["_resolve"] = lambda _path: _typed_dynamic_quant_stub()
    inputs = {spec["name"]: _Tensor(spec["shape"]) for spec in occurrence["allocations"]
              if spec["direction"] == "input"}
    namespace["_invoke"](occurrence["call_plan"], inputs, {}, {}, occurrence["attrs"], {})
    bad_plan = copy.deepcopy(occurrence["call_plan"])
    bad_plan["keyword"]["quant_mode"]["value"] = 7
    with pytest.raises(AssertionError):
        namespace["_invoke"](bad_plan, inputs, {}, {}, occurrence["attrs"], {})


def test_r3_every_declared_precondition_kind_is_executable():
    catalog = json.loads((ROOT / "mindie_profiler" / "op_api_catalog.json").read_text())
    declared = {(entry["repro_recipe"].get("preconditions") or {}).get("kind")
                for entry in catalog["operators"].values()
                if isinstance(entry["repro_recipe"].get("preconditions"), dict)}
    declared.discard(None)
    assert declared <= SUPPORTED_PRECONDITION_KINDS
    bad_overrides = {
        "rms_norm": {"attrs": {"epsilon": 0}},
        "attention_geometry": {"attrs": {"head_num": 0}},
        "dst_type": {"attrs": {"dst_type": "bad"}},
        "routing_flags": {"attrs": {"expert_tokens_num_type": 9}},
        "tensor_list_spans": {"call_plan": {"keyword": {"x": {"kind": "tensor_list"}}}},
        "inplace_aliases": {"call_plan": {"mutable_aliases": ["q"]}},
    }
    for kind in sorted(declared):
        occurrence = {"preconditions": {"kind": kind}, "attrs": {},
                      "allocations": [], "call_plan": {}, "padding": {}}
        occurrence.update(copy.deepcopy(bad_overrides.get(kind, {})))
        problems = precondition_problems(occurrence)
        assert problems, kind
        assert all(problem["code"] != "unhandled_precondition" for problem in problems)


# ---------------------------------------------------------------- R4 / R5
def test_r4_output_span_deficit_blocks_binding_and_consumption():
    binding = bind_captured_occurrence(_gmm_row(out_lengths=2))
    assert binding["slot_status"] != "bound"
    assert binding["status"] != "bound"
    assert binding["conservation"]["exact"] is False
    assert binding["conservation"]["span_deficit_count"] == 1
    assert {"code": "span_deficit", "name": "out", "declared": 2,
            "captured": 1} in binding["issues"]
    with pytest.raises(Exception):
        _compact_occurrence(binding)


def test_r5_absent_tensor_list_item_never_allocates():
    binding = bind_captured_occurrence(_gmm_row(x_slot={
        "shape": [64, 128], "dtype": "BF16", "layout": "ND", "present": False}))
    assert binding["status"] != "bound"
    assert any(issue["code"] == "tensor_list_item_invalid"
               for issue in binding["issues"])
    allocations, problems = _slot_allocations(binding)
    assert not [spec for spec in allocations if spec["name"] == "x"]
    assert any(problem["code"] == "allocation_absent_tensor" for problem in problems)
    with pytest.raises(Exception):
        _compact_occurrence(binding)


def test_r5_tensor_list_bad_layout_blocks_binding():
    row = _gmm_row(x_slot={"shape": [64, 128], "dtype": "BF16",
                           "layout": "NOT_A_LAYOUT"})
    binding = bind_captured_occurrence(row)
    assert binding["status"] != "bound"
    assert any(issue["code"] == "layout_not_declared" for issue in binding["issues"])
    x_record = next(record for record in binding["inputs"] if record["name"] == "x")
    assert x_record["usable"] is False
    with pytest.raises(Exception):
        _compact_occurrence(binding)


# --------------------------------------------------------------------- R6
def test_r6_sim_validates_groups_before_explicit_logical_tokens():
    predicted = {"total_ms": 10, "ops": [
        {"name": "X", "stream": 0, "start_ms": 0, "duration_ms": 10}]}
    captured = copy.deepcopy(predicted)
    result = attribute_diff(predicted, captured, cann_version="9.0", padding={
        "aclnnGroupedMatmulV4": {
            "bucket_tokens": 128, "logical_tokens": 73,
            "bound_args": {"group_list": [32, 30, 73]}}})
    assert result["status"] == "partial"
    assert result["padding"]["valid"] is False
    charge = result["padding"]["charges"][0]
    assert charge["charged_tokens"] == 0
    assert any(item["code"] == "group_list_not_monotone"
               for item in charge["violations"])


def test_r6_physical_t_extent_beats_bucket_override():
    row = fa_row(attrs={**fa_row()["attrs"], "bucket_tokens": 1000,
                        "actual_seq_q_len": [999]})
    binding = bind_captured_occurrence(row)
    assert binding["status"] != "bound"
    assert binding["padding"]["valid"] is False
    assert any(item["code"] == "sequence_q_exceeds_extent"
               for item in binding["padding"]["violations"])


def test_r6_bsh_per_sequence_bounds_accept_legal_non_increasing_lengths():
    rejected = bind_captured_occurrence(_bsh_fa_row([6, 0]))
    assert rejected["status"] != "bound"
    assert any(item["code"] == "sequence_q_exceeds_per_sequence_extent"
               for item in rejected["padding"]["violations"])
    accepted = bind_captured_occurrence(_bsh_fa_row([3, 2]))
    assert accepted["status"] == "bound"
    occurrence = _compact_occurrence(accepted)
    assert occurrence["status"] == "ready"
    assert occurrence["checks"]["sequence_per_item_bounds"] is True


# ---------------------------------------------------------------- R7 / R8
def test_r7_allocated_pages_cannot_be_inflated_by_attributes():
    table = [[9999 + index for index in range(16)] for _ in range(16)]
    row = _paged_row(table_values=table)
    row["attrs"]["num_blocks"] = 20000
    binding = bind_captured_occurrence(row)
    occurrence = _compact_occurrence(binding)
    assert occurrence["status"] == "blocked"
    assert occurrence["metadata"]["checks"]["allocated_pages"] == 256
    assert occurrence["metadata"]["checks"]["page_capacity_source"] == "kv_cache.shape[0]"
    assert occurrence["checks"]["block_table_in_bounds"] is False
    assert occurrence["checks"]["metadata_installable"] is False


def test_r7_routing_expert_indices_are_bounded_after_substitution():
    binding = bind_captured_occurrence(_moe_row([9999] * 16))
    occurrence = _compact_occurrence(binding)
    assert occurrence["status"] == "blocked"
    assert occurrence["checks"]["expert_ids_in_bounds"] is False
    install = next(item for item in occurrence["metadata"]["install"]
                   if item["tensor"] == "expert_idx")
    assert install["captured"] is True
    assert install["captured_valid"] is False
    assert install["values"] == [9999] * 16


def test_r8_captured_value_count_must_equal_numel():
    binding = bind_captured_occurrence(_rms_row([7]))
    assert binding["status"] == "bound"
    with pytest.raises(Exception) as excinfo:
        generate_single_op_reproducer(binding)
    assert "numel" in str(excinfo.value) or "captured" in str(excinfo.value)
    nested = bind_captured_occurrence(_rms_row([[7]]))
    with pytest.raises(Exception):
        _compact_occurrence(nested)


# ---------------------------------------------------------------- R9 / R10
def _probe_plan(warmup=5):
    return build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096], ops=["all_reduce"],
        iterations=2, warmup=warmup, duration_s=60.0,
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1],
                             "protocol": "HCCS"}]})


def test_r9_allocation_failure_takes_the_same_shared_decision_path():
    plan = _probe_plan()
    rank0 = _probe_run(plan, 0, {2: 0})
    rank1 = _probe_run(plan, 1, {}, fail_alloc=True)
    assert rank0[1].log == rank1[1].log == [1, 1, 0]
    assert rank0[1].data == rank1[1].data == 0
    assert rank0[0] == rank1[0] == 2
    assert "simulated allocation failure" in rank1[2]


def test_r10_warmup_iterations_execute_before_timed_samples():
    plan = _probe_plan(warmup=5)
    code, dist, output = _probe_run(plan, 0, {})
    assert code == 0
    assert dist.data == 1 + 5 + 2
    # Two timed post-telemetry wall gates plus one final wall-budget gate.
    assert dist.decisions == 1 + 3 + 2 * 5 + 2 * 2 + 2 + 1
    samples = [json.loads(line) for line in output.splitlines()
               if line.startswith("{")]
    timed = [sample for sample in samples
             if sample.get("schema") == "mindie-fabric-probe-sample/2"]
    assert len(timed) == 2
    assert all(sample["warmup"] == 5 and sample["iterations"] == 2
               for sample in timed)


def test_r10_live_deadline_aborts_after_a_delayed_allocation():
    plan = _probe_plan(warmup=5)
    plan["deadline"]["measurement_budget_s"] = 1.0
    leader = _probe_run(plan, 0, {}, advance_alloc=2.0)
    peer = _probe_run(plan, 1, {2: 0})
    assert leader[1].log == peer[1].log == [1, 1, 0]
    assert leader[1].data == peer[1].data == 0
    assert leader[0] == peer[0] == 2
    assert '"reason": "deadline"' in leader[2]
    assert "unmeasured" in leader[2]
    assert "mindie-fabric-probe-sample/2" not in leader[2]


# --------------------------------------------------------------------- R11
def _fit_samples(alpha=8.0, beta=0.1, **extra):
    return [{"tier": "intra_node_hccs", "op": "all_reduce", "bytes": size,
             "latency_us": alpha + beta * size / 1000.0, "group_size": 8,
             "protocol": "HCCS", **extra}
            for size in (4096, 65536, 1048576)]


def test_r11_missing_affirmative_evidence_cannot_calibrate_or_override():
    plan = build_fabric_probe_plan(world_size=16, ranks_per_node=8, duration_s=60)
    profile = fit_calibrated_fabric_profile(plan, _fit_samples())
    assert profile["status"] == "partial"
    assert profile["usable_for_link_override"] is False
    assert profile["topology_verified"] is False
    reasons = {item["reason"] for item in profile["unqualified_samples"]}
    assert "validated_absent" in reasons
    explicit_source = {**plan, "topology_source": "unverified_rank_group",
                       "physical_verification": True,
                       "topology_label": "explicit_topology"}
    profile = fit_calibrated_fabric_profile(
        explicit_source, _fit_samples(validated=True, rank=0,
                                      group_ranks=list(range(8))))
    assert profile["status"] == "partial"
    assert profile["usable_for_link_override"] is False

def test_r11_affirmative_evidence_and_verified_topology_can_calibrate():
    plan = build_fabric_probe_plan(
        world_size=8, ranks_per_node=8, duration_s=60,
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": list(range(8)),
                             "protocol": "HCCS"}]})
    profile = fit_calibrated_fabric_profile(
        plan, _fit_samples(validated=True, rank=0, group_ranks=list(range(8))))
    assert profile["status"] == "calibrated"
    assert profile["topology_verified"] is True
    assert profile["usable_for_link_override"] is True

# --------------------------------------------------------------------- R12
def test_r12_cold_verification_is_per_sweep_not_cumulative():
    namespace = exec_script(generate_single_op_reproducer(paged_binding())["script"])
    undersized = namespace["_cache_label"](1, 32 * 1024 * 1024, 50,
                                           50 * 1024 * 1024)
    assert undersized["cold_verified"] is False
    assert undersized["per_sweep_bytes"] == 1024 * 1024
    sized = namespace["_cache_label"](1, 32 * 1024 * 1024, 50,
                                      50 * 1024 * 1024, 32 * 1024 * 1024)
    assert sized["cold_verified"] is True

def test_r12_diff_clock_derating_has_no_thermal_inference():
    predicted = {"total_ms": 10, "ops": [
        {"name": "A", "stream": 0, "start_ms": 0, "duration_ms": 10}]}
    captured = {"total_ms": 10, "aic_mhz": 1000, "nominal_aic_mhz": 1800,
                "ops": [{"name": "A", "stream": 0, "start_ms": 0,
                         "duration_ms": 10}]}
    result = attribute_diff(predicted, captured, launch_overhead_us=0)
    clock = result["kernel_roofline_and_clock"]
    assert clock["clock_ratio_below_nominal"] is True
    assert clock["thermal_attribution"] == "not_measured"
    assert clock["temperature_telemetry"] is False
    assert clock["thermal_throttled"] is None

# --------------------------------------------------------------------- R13
def test_r13_stored_op_uid_and_raw_indices_are_preserved(tmp_path):
    row = _paged_row()
    row.update({"op_uid": "capture-uid-1", "stream": 0, "start_ms": 0,
                "duration_ms": 12})
    capture = {"run_id": "run-1", "total_ms": 12,
               "rows": [None, row]}
    predicted = {"total_ms": 10, "ops": [
        {"name": "aclnnPagedAttention", "stream": 0, "start_ms": 0,
         "duration_ms": 10}]}
    result = attribute_diff(predicted, capture, launch_overhead_us=0)
    offender = result["kernel_roofline_and_clock"]["top_offenders"][0]
    assert offender["op_uid"] == "capture-uid-1"
    assert offender["raw_op_index"] == 1
    assert len(extract_raw_rows(capture)) == 2
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(capture))
    canonical = _op_uid("run-1", {"rank": 0, "step": 0, "stream": 0,
                                  "abi_digest": "", "raw_op_index": 1})
    for uid in ("capture-uid-1", canonical):
        args = types.SimpleNamespace(
            row=None, capture=str(path), op_name="aclnnPagedAttention",
            occurrence_index=None, index=None, version="8.0", op_uid=uid)
        binding, index, _ = _row_from_args(args)
        assert index == 1
        assert binding["operator"] == "aclnnPagedAttention"
    bad = types.SimpleNamespace(
        row=None, capture=str(path), op_name=None, occurrence_index=0,
        index=None, version="8.0", op_uid=None)
    with pytest.raises(Exception):
        _row_from_args(bad)

# --------------------------------------------------------------------- R14
def test_r14_complete_mcp_envelope_is_measured_after_assembly():
    envelope = registry_mcp("inspect_op_abi",
                            {"op_name": "aclnnPagedAttention",
                             "cann_version": "8.0"})
    body = {key: value for key, value in envelope.items() if key != "receipt"}
    assert estimate_tokens(envelope) <= 250
    assert envelope["receipt"]["within_budget"] is True
    assert envelope["receipt"]["token_estimate"] == estimate_tokens(body)
    full = inspect_op_abi("aclnnPagedAttention", cann_version="8.0")
    assert full["receipt"]["within_budget"] is True
    assert estimate_tokens(full) <= full["receipt"]["token_limit"]

def test_r14_per_issue_details_are_truncated_to_the_budget():
    issues = [{"code": "x", "slot": index, "name": f"tensor_{index}",
               "detail": "D" * 1200} for index in range(8)]
    envelope = bounded_envelope({"schema": "s", "status": "blocked",
                                 "issues": issues}, limit=3000, list_limit=8)
    assert len(envelope["issues"]) == 8
    assert all(len(item["detail"]) < 1200 for item in envelope["issues"])
    assert envelope["receipt"]["within_budget"] is True
    assert estimate_tokens(envelope) <= 3000

def test_r14_artifact_directories_are_invocation_addressed():
    binding = paged_binding()
    first = call_mcp_tool("repro_op", {"occurrence": binding, "iters": 5})
    second = call_mcp_tool("repro_op", {"occurrence": binding, "iters": 50})
    first_path = Path(first["artifact_path"])
    second_path = Path(second["artifact_path"])
    try:
        assert first_path != second_path
        assert (hashlib.sha256(first_path.read_bytes()).hexdigest()
                != hashlib.sha256(second_path.read_bytes()).hexdigest())
        first_manifest = json.loads(Path(first["manifest_path"]).read_text())
        second_manifest = json.loads(Path(second["manifest_path"]).read_text())
        assert first_manifest["gate"]["iters"] == 5
        assert second_manifest["gate"]["iters"] == 50
        assert first["repro_sha256"] != second["repro_sha256"]
    finally:
        shutil.rmtree(first_path.parent, ignore_errors=True)
        shutil.rmtree(second_path.parent, ignore_errors=True)

def test_r15_touched_modules_keep_the_documented_hygiene_contract():
    targets = [
        "mindie_profiler/op_abi_attributes.py", "mindie_profiler/op_abi_binding.py",
        "mindie_profiler/op_api_registry.py", "mindie_profiler/repro_values.py",
        "mindie_profiler/repro_op.py", "mindie_profiler/repro_preconditions.py",
        "mindie_profiler/repro_metadata.py", "mindie_profiler/token_budget.py",
        "mindie_profiler/repro_script_template.py",
        "mindie_profiler/fabric_probe.py",
        "mindie_profiler/fabric_probe_script_template.py",
        "mindie_profiler/fabric_probe_fit.py",
        "mindie_sim/diff_trace_replay.py", "mindie_sim/diff_trace.py",
        "tests/nr_s6_round3_probe.py", "tests/test_nr_s6_round3_closure.py",
        "tests/nr_s6_round4_probe.py", "tests/test_nr_s6_round4_closure.py",
    ]
    for relative in targets:
        import mindie_sim
        sim_root = Path(mindie_sim.__file__).resolve().parents[1]
        target_path = (ROOT / relative) if (ROOT / relative).exists() else (sim_root / relative)
        payload = target_path.read_bytes()
        assert b"\r" not in payload, relative
        text = payload.decode("utf-8")
        assert len(text.splitlines()) < 750, relative
        header = "\n".join(text.splitlines()[:30])
        for marker in ("[Role]", "[Invariants]", "[Timeouts & Locks]",
                       "[Side-Effect Policy]"):
            assert marker in header, (relative, marker)

@pytest.mark.parametrize("name,field", [("aclnnGroupedMatmulV4", "x_len"),
    ("aclnnGroupedMatmulV4", "weight_len"), ("MoeGatingTopKSoftmax", "k"),
    ("aclnnFlashAttentionVarLenScore", "head_num"), ("QuantLightningIndexer", "sparse_count"),
    ("aclnnGroupedMatmulV4", "tensor_list_lengths"), ("MoeInitRoutingV2", "expert_num"),
    ("aclnnPagedAttention", "block_size"), ("aclnnGroupedMatmulV4", "group_count")])
@pytest.mark.parametrize("bad", [True, False, "1", 1.5, -1, 2**63, 10**5000, -10**5000], ids=["true", "false", "string", "fraction", "negative", "excessive", "huge", "negative_huge"])
def test_r21_repro_count_attributes_rejected_before_hash(name, field, bad):
    import copy
    from test_nr_s6_round2_closure import _ready_bindings
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.repro_op import generate_single_op_reproducer
    from mindie_profiler.repro_mcp import call_mcp_tool
    from mindie_profiler.token_budget import estimate_tokens
    binding = copy.deepcopy(_ready_bindings()[name])
    binding["attrs"][field] = {"x": bad} if field == "tensor_list_lengths" else bad
    with pytest.raises(ProfilerUsageError):
        generate_single_op_reproducer(binding)
    result = call_mcp_tool("repro_op", {"occurrence": binding})
    assert result["status"] == "blocked" and result["receipt"]["within_budget"]
    assert estimate_tokens(result) <= 250

@pytest.mark.parametrize("field", ["inputs", "outputs"])
@pytest.mark.parametrize("bad", [True, False, "1", 1.5, -1, 2**63, 10**5000, -10**5000], ids=["true", "false", "string", "fraction", "negative", "excessive", "huge", "negative_huge"])
def test_r21_repro_shape_rejected_before_diagnostic(field, bad):
    import copy
    from nr_s6_support import paged_binding
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.repro_op import generate_single_op_reproducer
    from mindie_profiler.repro_mcp import call_mcp_tool
    from mindie_profiler.token_budget import estimate_tokens
    binding = copy.deepcopy(paged_binding())
    next(s for s in binding[field] if s.get("shape"))["shape"] = [bad]
    with pytest.raises(ProfilerUsageError):
        generate_single_op_reproducer(binding)
    result = call_mcp_tool("repro_op", {"occurrence": binding})
    assert result["status"] == "blocked" and estimate_tokens(result) <= 250

def test_r21_count_boundaries_and_bounded_diagnostics():
    from mindie_profiler.repro_values import bounded_shape, bounded_summary, validate_count_attributes
    from mindie_profiler.op_abi_attributes import attr_issue
    assert bounded_shape([0, 268435456]) == 0
    assert bounded_shape([268435456]) == 268435456
    validate_count_attributes({"x_len": 0, "weight_len": 1, "k": 1, "sparse_count": 0})
    for value in (10**5000, -10**5000, [-(10**5000)]):
        assert len(bounded_summary(value)) < 120
        for kind in ("int", "float", "bool", "str", "int_array"):
            assert attr_issue("k", kind, value)[0]

@pytest.mark.parametrize("field", ["input_shapes", "output_shapes"])
@pytest.mark.parametrize("sign", [-1, 1])
def test_r21_raw_shape_overflow_precedes_native_hash(field, sign):
    from test_nr_s6_round2_closure import rms_norm_row
    from mindie_profiler.events import ProfilerUsageError
    from mindie_profiler.op_api_registry import bind_captured_occurrence
    row = rms_norm_row()
    row[field][0]["shape"] = [sign * 10**5000]
    with pytest.raises(ProfilerUsageError):
        bind_captured_occurrence(row)
