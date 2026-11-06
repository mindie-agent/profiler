"""Retained A3 prefill kernels fix attention and TP collective boundaries.

[Role] Exercise the packaged native profile on a genuine full-chunk capture.
[Invariants] Native count/sum fixes the response; Body durations, case names
  and capture paths select nothing. Both boundaries change together, and an
  unobserved or ambiguous state preserves the complete caller input.
[Timeouts & Locks] A finite target graph and two Body predictions per module;
  no waits, devices, network or capture access.
[Side-Effect Policy] Runtime homes are isolated by the repository conftest.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")
from mindie_sim import graph_costs, predict, target_operators  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from prefill_native_observations import (  # noqa: E402
    PROFILE_PATH, apply_prefill_native_observations)
from prefill_native_builder import (  # noqa: E402
    _attention_abi_slots, _attention_contract, _spread_summary)

FIXTURE = ROOT / "tests/fixtures/native_observations/a3_qwen35_prefill_400k_native.json"
GEOMETRY = {"phase": "prefill", "tokens": 8064, "context": 201600, "sequences": 1}
COLLECTIVE_COUNTS = {"linear_reduce": 30, "catalog_tp_allreduce": 10, "ring_allreduce": 40}


def retained():
    return json.loads(FIXTURE.read_text())


def profile():
    return json.loads(PROFILE_PATH.read_text())


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _keys(item)


def part(fixture, forward):
    return next(row for row in fixture["parts"] if row["forward"] == forward)


def attention_us(raw, geometry=GEOMETRY):
    totals = []
    for op in target_operators(raw, **geometry):
        if op.recipe != "flash_attention":
            continue
        totals.append(graph_costs(raw, (op,), isolated=False,
                                  external_inputs={key: 0 for key in op.deps})["duration_ms"] * 1000)
    return totals


def collective_us(raw, geometry=GEOMETRY):
    seen, result = set(), {}
    for op in target_operators(raw, **geometry):
        if op.recipe not in COLLECTIVE_COUNTS or op.recipe in seen:
            continue
        seen.add(op.recipe)
        result[op.recipe] = graph_costs(
            raw, (op,), isolated=False,
            external_inputs={key: 0 for key in op.deps})["duration_ms"] * 1000
    return result


def operator_us(raw, recipe):
    op = next(item for item in target_operators(raw, **GEOMETRY) if item.recipe == recipe)
    return graph_costs(raw, (op,), isolated=False,
                       external_inputs={key: 0 for key in op.deps})["duration_ms"] * 1000


def old_allreduce_floor(raw):
    rules = [rule for rule in raw["runtime"]["kernels"]["service_regimes"]
             if rule.get("match", {}).get("phase") == "prefill"
             and rule.get("match", {}).get("family") == "allreduce"]
    assert len(rules) == 1
    return rules[0]["id"], rules[0]["response"]["fixed_us"]


def test_full_chunk_imports_native_boundaries_and_removes_the_capture_floor():
    fixture = retained()
    raw, original = fixture["raw_case"], deepcopy(fixture["raw_case"])
    old_id, old_floor = old_allreduce_floor(raw)
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert raw == original
    assert provenance["status"] == "applied"
    assert provenance["replaced_rule_ids"] == [old_id]
    assert provenance["imported_rule_count"] == 4
    assert {row["id"]: row["occurrences"] for row in provenance["matched_domains"]} == {
        "a3-qwen35-prefill-native-fai-q8064": 10,
        "a3-qwen35-prefill-native-ar-linear-reduce": 30,
        "a3-qwen35-prefill-native-ar-catalog-tp-allreduce": 10,
        "a3-qwen35-prefill-native-ar-ring-allreduce": 40,
    }
    document = profile()
    attention = {key: value for key, value in document["native_observations"]
                 ["flash_attention"]["knots"]}
    native = part(fixture, 25)
    assert native["context"] == GEOMETRY["context"] and native["tokens"] == GEOMETRY["tokens"]
    anchored = attention[GEOMETRY["context"] + GEOMETRY["tokens"]]
    for value in attention_us(adapted):
        assert value == pytest.approx(anchored, abs=1e-6)
    assert anchored == pytest.approx(native["attention"]["sum_us"] / 10, rel=0.02)
    us_per_call = document["native_observations"]["allreduce"]["us_per_call"]
    for recipe, per_call in collective_us(adapted).items():
        assert per_call == pytest.approx(us_per_call, abs=1e-6)
        assert per_call != pytest.approx(old_floor)
    assert operator_us(adapted, "flash_attention") == pytest.approx(anchored)
    # The native floor retains the measured forward sum, not a wait estimate.
    native_collective = sum(row["sum_us"] for row in native["collectives"].values())
    assert native_collective / 80 == pytest.approx(us_per_call, rel=0.05)
    for recipe in ("balanced_grouped_gate_up", "rmsnorm"):
        assert operator_us(adapted, recipe) == pytest.approx(operator_us(raw, recipe))


def test_curve_units_and_monotone_context_work_match_retained_chunks():
    fixture = retained()
    knots = profile()["native_observations"]["flash_attention"]["knots"]
    assert [row[0] for row in knots] == [8064 * (index + 1) for index in range(len(knots))]
    assert all(right[1] > left[1] for left, right in zip(knots, knots[1:]))
    anchors = dict(knots)
    for row in fixture["parts"]:
        if row["tokens"] != 8064:
            continue
        native_call = row["attention"]["sum_us"] / 10
        assert anchors[row["context"] + row["tokens"]] == pytest.approx(native_call, rel=0.02)
        assert row["attention"]["count"] == 10


@pytest.mark.parametrize("geometry,reason", (
    ({"phase": "prefill", "tokens": 4608, "context": 395136, "sequences": 1},
     "prefill_chunk_rows_outside_observed_domain"),
    ({"phase": "prefill", "tokens": 3072, "context": 193536, "sequences": 1},
     "prefill_chunk_rows_outside_observed_domain"),
    ({"phase": "prefill", "tokens": 8064, "context": 393216, "sequences": 1},
     "prefill_context_outside_observed_domain"),
    ({"phase": "prefill", "tokens": 8064, "context": 201600, "sequences": 2},
     "sequence_partition_outside_observed_domain"),
    ({"phase": "decode", "tokens": 8064, "context": 201600, "sequences": 1},
     "phase_outside_observed_domain"),
))
def test_tail_and_unobserved_states_keep_the_complete_input(geometry, reason):
    fixture = retained()
    raw, original = fixture["raw_case"], deepcopy(fixture["raw_case"])
    adapted, provenance = apply_prefill_native_observations(raw, **geometry)
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"] == reason
    assert adapted == raw == original


@pytest.mark.parametrize("condition,reason", (
    ("hardware", "hardware_outside_observed_domain"),
    ("parallelism", "parallelism_outside_observed_domain"),
    ("layers", "model_geometry_outside_observed_domain"),
    ("layer_mix", "layer_geometry_outside_observed_domain"),
    ("quantization", "quantization_outside_observed_domain"),
    ("moe_recipe", "runtime_outside_observed_domain"),
    ("routing", "runtime_outside_observed_domain"),
    ("lowering", "required_source_lowering_not_selected"),
    ("sequence_parallel", "sequence_parallel_outside_observed_domain"),
    ("device_rate", "physical_rates_or_topology_outside_observed_domain"),
    ("placement", "physical_rates_or_topology_outside_observed_domain"),
    ("collective_parallel", "parallelism_outside_observed_domain"),
))
def test_source_domain_guards_preserve_the_input(condition, reason):
    fixture = retained()
    raw = fixture["raw_case"]
    if condition == "hardware":
        raw["machine"]["sku"] = "Ascend910B4"
        raw["machine"].pop("hardware_key", None)
    elif condition == "parallelism":
        raw["runtime"]["tp"] = 4
        raw["runtime"]["ep"] = 4
    elif condition == "layers":
        raw["model"]["layers"] = 8
        raw["model"]["layer_plans"] = raw["model"]["layer_plans"][:8]
    elif condition == "layer_mix":
        plan = next(item for item in raw["model"]["layer_plans"]
                    if item.get("attention") == "gqa")
        plan["attention"] = "gdn"
    elif condition == "quantization":
        raw["model"]["quant"]["weight_format"] = "bf16"
    elif condition == "moe_recipe":
        raw["runtime"]["moe_recipe"] = "tp_join_reduce"
    elif condition == "routing":
        raw["runtime"]["routing"] = {"policy": "expected"}
    elif condition == "sequence_parallel":
        raw["runtime"]["kernels"]["sequence_parallel"] = True
    elif condition == "device_rate":
        raw["machine"].setdefault("device", {}).setdefault("rates", {})["hbm"] = 1e6
    elif condition == "placement":
        raw["machine"]["ranks_per_node"] = 4
    elif condition == "collective_parallel":
        raw["runtime"]["cp"] = 2
    else:
        raw["runtime"]["lowering_passes"] = []
    original = deepcopy(raw)
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"] == reason
    assert adapted == raw == original


def test_old_rule_that_also_spans_other_calls_is_not_deleted():
    fixture = retained()
    raw, original = fixture["raw_case"], deepcopy(fixture["raw_case"])
    raw["runtime"]["kernels"]["service_regimes"].append({
        "id": "broad-prefill-response", "match": {"phase": "prefill"},
        "response": {"fixed_us": 1.0}})
    original["runtime"]["kernels"]["service_regimes"].append({
        "id": "broad-prefill-response", "match": {"phase": "prefill"},
        "response": {"fixed_us": 1.0}})
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"] == "existing_response_spans_native_and_other_boundaries"
    assert adapted == raw == original


def test_broad_rule_without_the_observed_phase_blocks_deletion():
    fixture = retained()
    raw, original = fixture["raw_case"], deepcopy(fixture["raw_case"])
    rule = {"id": "cross-phase-allreduce", "match": {"family": "allreduce"},
            "response": {"fixed_us": 1.0}}
    raw["runtime"]["kernels"]["service_regimes"].append(deepcopy(rule))
    original["runtime"]["kernels"]["service_regimes"].append(deepcopy(rule))
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"].startswith("foreign_response_matches_native_boundary")
    assert adapted == raw == original


def test_changed_source_identity_does_not_change_the_physical_input(tmp_path):
    fixture = retained()
    raw = fixture["raw_case"]
    document = json.loads(PROFILE_PATH.read_text())
    document["id"] = "same-physical-profile-other-sources"
    document["training_sources"] = [
        {"id": "renamed-training-capture", "path": "/elsewhere/other.csv",
         "sha256": "0" * 64}]
    document["validation_sources"] = [
        {"id": "renamed-heldout-capture", "path": "/elsewhere/heldout.csv",
         "sha256": "1" * 64}]
    for rule in document["service_regimes"]:
        rule["provenance"]["training_source_ids"] = ["renamed-training-capture"]
        rule["provenance"]["profile_id"] = document["id"]
    target = tmp_path / "prefill_native_other_sources.json"
    target.write_text(json.dumps(document))
    default, default_provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    renamed, renamed_provenance = apply_prefill_native_observations(
        raw, profile_path=target, **GEOMETRY)
    assert default == renamed
    assert default_provenance["profile"]["sha256"] != renamed_provenance["profile"]["sha256"]
    assert renamed_provenance["imported_rules"][0]["training_source_ids"] == [
        "renamed-training-capture"]
    imported = [rule for rule in renamed["runtime"]["kernels"]["service_regimes"]
                if rule["id"].startswith("a3-qwen35-prefill-native-")]
    assert len(imported) == 4
    for rule in imported:
        assert set(rule) == {"id", "match", "coordinates", "domain", "response"}
        assert "renamed-training-capture" not in set(_strings(rule))


def test_explicit_foreign_phase_scoped_response_is_not_overridden():
    fixture = retained()
    raw, original = fixture["raw_case"], deepcopy(fixture["raw_case"])
    rule = {"id": "user-prefill-allreduce-override",
            "match": {"phase": "prefill", "family": "allreduce"},
            "response": {"fixed_us": 1234.0}}
    raw["runtime"]["kernels"]["service_regimes"].append(deepcopy(rule))
    original["runtime"]["kernels"]["service_regimes"].append(deepcopy(rule))
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"] == ("foreign_response_matches_native_boundary:"
                                    "user-prefill-allreduce-override")
    assert adapted == raw == original


def test_foreign_rule_reusing_an_imported_identifier_is_rejected():
    fixture = retained()
    raw = fixture["raw_case"]
    raw["runtime"]["kernels"]["service_regimes"].append({
        "id": "a3-qwen35-prefill-native-ar-ring-allreduce",
        "match": {"phase": "prefill", "family": "allreduce"},
        "response": {"fixed_us": 1.0}})
    original = deepcopy(raw)
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"].startswith("foreign_response_matches_native_boundary")
    assert adapted == raw == original


def test_scoped_alltoall_partition_plus_quantized_transport_stays_in_domain():
    # Track C's physical A3 declaration: TP-slice token partition and a
    # separate INT8 payload / FP32 scale / INT32 histogram transport.
    fixture = retained()
    raw = fixture["raw_case"]
    kernels = raw["runtime"]["kernels"]
    kernels["moe_token_partition"] = {
        "kind": "vllm_ascend_alltoall_tp_slice", "padding": "none",
        "gather_output_materialization": "per_rank_copy"}
    kernels["moe_transport"] = {
        "kind": "separate_quantized_payload", "dispatch_dtype": "int8",
        "payload_dtype": "int8", "scale_dtype": "fp32",
        "scale_granularity": "row", "histogram_dtype": "int32"}
    baseline, _ = apply_prefill_native_observations(fixture["raw_case"], **GEOMETRY)
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "applied"
    assert (adapted["runtime"]["kernels"]["service_regimes"] ==
            baseline["runtime"]["kernels"]["service_regimes"])
    assert adapted["runtime"]["kernels"]["moe_token_partition"] == (
        kernels["moe_token_partition"])
    assert adapted["runtime"]["kernels"]["moe_transport"] == kernels["moe_transport"]
    broken = deepcopy(raw)
    broken["machine"].setdefault("device", {}).setdefault("rates", {})["hbm"] = 1e6
    rejected, rejected_provenance = apply_prefill_native_observations(broken, **GEOMETRY)
    assert rejected_provenance["reason"] == (
        "physical_rates_or_topology_outside_observed_domain")
    assert rejected == broken


def test_historical_response_is_owned_only_by_its_exact_physical_contract():
    fixture = retained()
    raw = fixture["raw_case"]
    historical_id, _ = old_allreduce_floor(raw)
    baseline, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "applied" and historical_id in provenance["replaced_rule_ids"]
    edited = deepcopy(raw)
    rule = next(item for item in edited["runtime"]["kernels"]["service_regimes"]
                if item["id"] == historical_id)
    rule["response"] = {"fixed_us": 123.456}
    original = deepcopy(edited)
    kept, conflict = apply_prefill_native_observations(edited, **GEOMETRY)
    assert conflict["status"] == "not_applicable"
    assert conflict["reason"] == (
        "foreign_response_matches_native_boundary:" + historical_id)
    assert kept == edited == original
    assert any(item["id"] == historical_id
               for item in kept["runtime"]["kernels"]["service_regimes"])
    known_variant = deepcopy(raw)
    next(item for item in known_variant["runtime"]["kernels"]["service_regimes"]
         if item["id"] == historical_id)["response"] = {"fixed_us": 2500.0}
    variant_result, variant_provenance = apply_prefill_native_observations(
        known_variant, **GEOMETRY)
    assert variant_provenance["status"] == "applied"
    assert historical_id in variant_provenance["replaced_rule_ids"]
    provenance_only = deepcopy(raw)
    next(item for item in provenance_only["runtime"]["kernels"]["service_regimes"]
         if item["id"] == historical_id)["provenance"] = {"origin": "caller"}
    provenance_result, provenance_status = apply_prefill_native_observations(
        provenance_only, **GEOMETRY)
    assert provenance_status["status"] == "applied"
    assert provenance_status["replaced_rule_ids"] == [historical_id]
    assert baseline["runtime"]["kernels"]["service_regimes"] == (
        provenance_result["runtime"]["kernels"]["service_regimes"])


def _contract_row(contract):
    row = {"Type": contract["kind"]}
    for side, key in (("Input", "inputs"), ("Output", "outputs")):
        row[side + " Shapes"] = ";".join(",".join(map(str, slot[0]))
                                         for slot in contract[key])
        row[side + " Data Types"] = ";".join(slot[1] for slot in contract[key])
        row[side + " Formats"] = ";".join(slot[2] for slot in contract[key])
    return row


def _mutate_contract(row, mutation, paged):
    row = deepcopy(row)
    if mutation == "v_dtype":
        slots = row["Input Data Types"].split(";")
        slots[2] = "fp32"
        row["Input Data Types"] = ";".join(slots)
    elif mutation == "v_layout":
        slots = row["Input Formats"].split(";")
        slots[2] = "FRACTAL_NZ"
        row["Input Formats"] = ";".join(slots)
    elif mutation == "length_dtype":
        slots = row["Input Data Types"].split(";")
        slots[4] = "fp32"
        row["Input Data Types"] = ";".join(slots)
    elif mutation == "length_shape":
        slots = row["Input Shapes"].split(";")
        slots[5] = "2"
        row["Input Shapes"] = ";".join(slots)
    elif mutation == "dense_k_rows":
        slots = row["Input Shapes"].split(";")
        slots[1] = slots[2] = "1,1,256"
        row["Input Shapes"] = ";".join(slots)
    elif mutation == "block_table_dtype":
        slots = row["Input Data Types"].split(";")
        slots[6] = "int64"
        row["Input Data Types"] = ";".join(slots)
    elif mutation == "block_table_capacity":
        slots = row["Input Shapes"].split(";")
        slots[6] = "1,1"
        row["Input Shapes"] = ";".join(slots)
    elif mutation == "larger_capacity":
        slots = row["Input Shapes"].split(";")
        slots[6] = "1,9999"
        row["Input Shapes"] = ";".join(slots)
    elif mutation == "paged_capacity":
        slots = row["Input Shapes"].split(";")
        slots[1] = slots[2] = "1,128,256"
        row["Input Shapes"] = ";".join(slots)
    else:
        slots = row["Output Shapes"].split(";")
        slots[1] = "999,999"
        row["Output Shapes"] = ";".join(slots)
    return row


def test_builder_rejects_incompatible_attention_value_length_and_lse_slots():
    document = profile()
    contracts = document["native_observations"]["flash_attention"]["tensor_abi"]
    for contract in contracts:
        paged = contract["kv_layout"] == "paged"
        context = 201600 if paged else 0
        row = _contract_row(contract)
        _attention_contract(row, 8064, paged=paged, context=context)
        mutations = ["v_dtype", "v_layout", "length_dtype", "length_shape", "lse_shape"]
        mutations.append("block_table_dtype" if paged else "dense_k_rows")
        if paged:
            mutations += ["paged_capacity", "block_table_capacity"]
        for mutation in mutations:
            with pytest.raises(ValueError, match="attention_"):
                _attention_contract(_mutate_contract(row, mutation, paged), 8064,
                                    paged=paged, context=context)
        if paged:
            _attention_contract(_mutate_contract(row, "larger_capacity", paged), 8064,
                                paged=paged, context=context)


def test_builder_rejects_divergent_heldout_attention_abi():
    document = profile()
    contracts = {row["kv_layout"]: row
                 for row in document["native_observations"]["flash_attention"]["tensor_abi"]}
    training = [{"query_rows": 8064,
                 "context": 0 if layout == "dense" else 201600,
                 "attention_tensor_abi": deepcopy(contracts[layout])}
                for layout in ("dense", "paged")]
    _attention_abi_slots(training, [])
    divergent = deepcopy(contracts["paged"])
    divergent["inputs"][2][1] = "fp32"
    with pytest.raises(ValueError, match="heldout_attention_tensor_abi"):
        _attention_abi_slots(training, [{"query_rows": 8064, "context": 201600,
                                         "attention_tensor_abi": divergent}])
    larger_capacity = deepcopy(contracts["paged"])
    larger_capacity["inputs"][1][0][0] = 40000
    larger_capacity["inputs"][2][0][0] = 40000
    larger_capacity["inputs"][6][0][1] = 4000
    _attention_abi_slots(training, [{"query_rows": 8064, "context": 201600,
                                     "attention_tensor_abi": larger_capacity}])
    short_table = deepcopy(contracts["paged"])
    short_table["inputs"][6][0][1] = 1
    with pytest.raises(ValueError, match="attention_block_table_capacity"):
        _attention_abi_slots(training, [{"query_rows": 8064, "context": 201600,
                                         "attention_tensor_abi": short_table}])
    with pytest.raises(ValueError, match="attention_block_table_capacity"):
        _attention_abi_slots([{"query_rows": 8064, "context": 201600,
                               "attention_tensor_abi": short_table}], [])
    exact_minimum = deepcopy(contracts["paged"])
    exact_minimum["inputs"][6][0][1] = 1638
    _attention_abi_slots(training, [{"query_rows": 8064, "context": 201600,
                                     "attention_tensor_abi": exact_minimum}])


def test_body_change_is_the_declared_native_boundary_delta_only():
    fixture = retained()
    raw = fixture["raw_case"]
    baseline = predict(raw, scope="body", event_limit=0, **GEOMETRY)["body_forward_ms"]
    adapted, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    assert provenance["status"] == "applied"
    native = predict(adapted, scope="body", event_limit=0, **GEOMETRY)["body_forward_ms"]
    before_attention = sum(attention_us(raw))
    after_attention = sum(attention_us(adapted))
    before = collective_us(raw)
    after = collective_us(adapted)
    before_collective = sum(count * before[recipe] for recipe, count in COLLECTIVE_COUNTS.items())
    after_collective = sum(count * after[recipe] for recipe, count in COLLECTIVE_COUNTS.items())
    assert (native - baseline) * 1000 == pytest.approx(
        (after_attention - before_attention) + (after_collective - before_collective), abs=1.0)
    assert abs(after_attention - before_attention) > 1000
    assert abs(after_collective - before_collective) > 100000


def test_repeated_import_is_identical_and_keeps_evidence_in_the_sidecar():
    fixture = retained()
    raw = fixture["raw_case"]
    first, provenance = apply_prefill_native_observations(raw, **GEOMETRY)
    second, again = apply_prefill_native_observations(first, **GEOMETRY)
    assert second == first and again["status"] == "applied"
    digest = hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest()
    assert provenance["profile"]["sha256"] == digest
    assert provenance["imported_rule_count"] == len(provenance["imported_rules"]) == 4
    for entry in provenance["imported_rules"]:
        assert entry["profile_sha256"] == digest
        assert entry["training_source_ids"]
    for rule in first["runtime"]["kernels"]["service_regimes"]:
        if rule["id"].startswith("a3-qwen35-prefill-native-"):
            assert set(rule) == {"id", "match", "coordinates", "domain", "response"}
            assert "provenance" not in rule


def test_heldout_captures_are_declared_and_absent_from_every_parameter():
    document = profile()
    training = {row["id"] for row in document["training_sources"]}
    validation = {row["id"] for row in document["validation_sources"]}
    assert training and validation and not training & validation
    assert retained()["source_case_id"] in training
    for rule in document["service_regimes"]:
        sources = set(rule["provenance"]["training_source_ids"])
        assert sources and sources <= training
        assert not sources & validation
    assert set(document["calibration"]["validation_capture_ids"]) == validation


def test_profile_records_native_abi_and_rejects_unobserved_source_claims():
    document = profile()
    flash = document["native_observations"]["flash_attention"]
    assert {row["kv_layout"] for row in flash["tensor_abi"]} == {"dense", "paged"}
    for row in flash["tensor_abi"]:
        assert row["inputs"][0][0] == [8064, 2, 256] and row["inputs"][0][1] == "bf16"
        assert row["inputs"][1][1] == "bf16" and row["inputs"][2][1] == "bf16"
        assert row["inputs"][2][2] == "ND"
        assert row["inputs"][4] == [[1], "int64", "ND"]
        assert row["inputs"][5] == [[1], "int64", "ND"]
        assert row["outputs"][1] == [[], "fp32", "ND"]
        assert all(slot[2] == "ND" for slot in row["inputs"])
        if row["kv_layout"] == "dense":
            assert row["inputs"][1][0] == [8064, 1, 256]
            assert row["inputs"][2][0] == [8064, 1, 256]
        else:
            assert row["inputs"][1][0][1:] == [128, 256]
            assert row["inputs"][6][1] == "int32"
    contracts = document["replaced_regime_contracts"]
    assert {rule["id"] for rule in contracts} == {
        "qwen35-a3-tp8-prefill-allreduce"}
    assert 3374.6 in {rule["response"]["fixed_us"] for rule in contracts}
    assert document["replaced_regime_contract_source"]["sha256"]
    assert document["calibration"]["heldout_relation"] == "repeat_geometry_cross_capture"
    assert document["calibration"]["heldout_context_generalization"] is False
    for rule in document["service_regimes"]:
        assert rule["match"]["physical_rates"]["resources"]["hbm"] > 0
        if rule["id"].endswith("fai-q8064"):
            assert rule["match"]["metadata.query_tile"] == 128
        else:
            assert rule["match"]["transport"]["collective"] == "allreduce"
            assert rule["match"]["local_shape"]
    collective = document["native_observations"]["allreduce"]
    assert collective["us_per_call"] * 80 == pytest.approx(
        collective["per_forward_total"]["mean_us"], rel=1e-6)
    assert set(collective["per_recipe_measurement"]) == set(COLLECTIVE_COUNTS)
    keys = set(_keys(document))
    assert "group_list" not in keys and "peer_window" not in keys
    assert document["calibration"]["body_error_used_for_selection"] is False
    fixture = retained()
    source = next(row for row in document["training_sources"]
                  if row["id"] == fixture["source_case_id"])
    assert source["sha256"] == fixture["source"]["sha256"]


def _attention_row(paged):
    if paged:
        shapes = "8064,2,256;34605,128,256;34605,128,256;2048,2048;1;1;1,3201"
        dtypes = "DT_BF16;DT_BF16;DT_BF16;INT8;INT64;INT64;INT32"
        formats = "ND;ND;ND;ND;ND;ND;ND"
    else:
        shapes = "8064,2,256;8064,1,256;8064,1,256;2048,2048;1;1"
        dtypes = "DT_BF16;DT_BF16;DT_BF16;INT8;INT64;INT64"
        formats = "ND;ND;ND;ND;ND;ND"
    return {"Type": "FusedInferAttentionScore", "Input Shapes": f'"{shapes}"',
            "Input Data Types": dtypes, "Input Formats": formats,
            "Output Shapes": '"8064,2,256;"', "Output Data Types": "DT_BF16;FLOAT",
            "Output Formats": "ND;ND"}


def test_builder_projects_the_complete_attention_tensor_abi():
    dense = _attention_contract(_attention_row(False), 8064, paged=False)
    paged = _attention_contract(_attention_row(True), 8064, paged=True)
    assert dense["kv_layout"] == "dense" and paged["kv_layout"] == "paged"
    for contract in (dense, paged):
        assert contract["inputs"][0][:2] == [[8064, 2, 256], "bf16"]
        assert contract["outputs"][0][:2] == [[8064, 2, 256], "bf16"]
        assert contract["outputs"][1][1] == "fp32"
    with pytest.raises(ValueError, match="attention_input_tensor_abi"):
        _attention_contract(_attention_row(True), 8064, paged=False)
    with pytest.raises(ValueError, match="attention_input_tensor_abi"):
        _attention_contract(_attention_row(False), 8064, paged=True)
    broken = _attention_row(False)
    broken["Input Data Types"] = "DT_BF16;DT_FP16;DT_BF16;INT8;INT64;INT64"
    with pytest.raises(ValueError, match="attention_input_tensor_abi"):
        _attention_contract(broken, 8064, paged=False)


def test_builder_spread_summary_counts_every_retained_call():
    summary = _spread_summary([3.0, 1.0, 2.0, 4.0])
    assert summary["count"] == 4 and summary["median_us"] == 2.5
    assert summary["min_us"] == 1.0 and summary["max_us"] == 4.0
