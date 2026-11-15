"""Exercise native A5 responses against retained declared tensor contracts.

[Role] Verify complete source-conditioned imports and domain exits.
[Invariants] Real retained input and observation means remain unchanged; partial
  physical matches never replace a five-kernel response family.
[Timeouts & Locks] Small local graphs only, no locks or remote operations.
[Side-Effect Policy] Runtime homes are isolated by conftest; no capture writes.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")
from mindie_sim import predict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from a5_native_observations import PROFILE_PATH, apply_a5_native_observations


@pytest.fixture
def retained_case():
    path = ROOT / "tests" / "fixtures" / "native_observations" / "a5_qwen35_tp4_q1.json"
    return json.loads(path.read_text())["raw_case"]


@pytest.mark.parametrize("sequences", (1, 4, 16))
def test_complete_native_domains_execute_observed_responses(retained_case, sequences):
    original = deepcopy(retained_case)
    imported, provenance = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=sequences,
    )
    assert provenance["status"] == "applied"
    assert len(provenance["matched_domains"]) == 5
    assert not provenance["observations_modified"]
    assert retained_case == original
    profile = json.loads(PROFILE_PATH.read_text())
    matched = {row["id"] for row in provenance["matched_domains"]}
    expected = {row["match"]["recipe"]: row["response"]["fixed_us"] / 1000
                for row in profile["rules"] if row["id"] in matched}
    previous = original["runtime"]["kernels"]["service_regimes"]
    remaining = [row for row in previous if row["id"] not in provenance["replaced_rule_ids"]]
    assert imported["runtime"]["kernels"]["service_regimes"][:len(remaining)] == remaining
    output = predict(imported, scope="body", phase="decode", tokens=1,
                     context=4096, sequences=sequences, event_limit=0)
    seen = set()
    for op in output["timeline"]:
        if op["recipe"] in expected:
            seen.add(op["recipe"])
            assert op["elapsed_ms"] == pytest.approx(expected[op["recipe"]])
    assert seen == expected.keys()
    normalizations = [op for op in output["timeline"] if op["recipe"] == "route_normalize"]
    assert len(normalizations) == 8 and all(op["elapsed_ms"] > 0 for op in normalizations)
    repeated, _ = apply_a5_native_observations(
        imported, phase="decode", tokens=1, context=4096, sequences=sequences,
    )
    assert repeated == imported


@pytest.mark.parametrize("geometry", (
    {"phase": "prefill", "tokens": 1, "sequences": 4},
    {"phase": "decode", "tokens": 4, "sequences": 1},
    {"phase": "decode", "tokens": 1, "sequences": 2},
))
def test_equal_total_rows_do_not_alias_unobserved_partitions(retained_case, geometry):
    imported, provenance = apply_a5_native_observations(retained_case, context=4096, **geometry)
    assert provenance["status"] == "not_applicable"
    assert imported == retained_case


@pytest.mark.parametrize("condition", ("projection_dtype", "graph", "caller", "stride"))
def test_partial_or_different_source_abi_preserves_all_original_rules(retained_case, condition):
    if condition == "projection_dtype":
        retained_case["model"]["quant"]["category_overrides"]["gdn.o"] = {
            "weight_format": "int8", "activation_format": "int8",
        }
    elif condition == "graph":
        retained_case["runtime"]["graph_mode"] = "none"
    else:
        caller = retained_case["runtime"]["kernels"]["lowerings"]["gdn_decode"]
        if condition == "caller":
            del retained_case["runtime"]["kernels"]["lowerings"]["gdn_decode"]
        else:
            caller["options"]["cache_index_row_stride"] = 1
    original = deepcopy(retained_case)
    imported, provenance = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
    )
    assert provenance["status"] == "not_applicable"
    assert imported == original == retained_case


def test_local_native_domains_do_not_depend_on_body_case_name_or_kv_length(retained_case):
    retained_case["name"] = "same physical native operators in an independent capture"
    imported, provenance = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=65536, sequences=4,
    )
    assert provenance["status"] == "applied"
    assert len(provenance["matched_domains"]) == 5
    assert imported["name"] == retained_case["name"]
    assert not provenance["calibration"]["native_binary_source_identity_verified"]


@pytest.mark.parametrize("condition", ("hbm", "compute", "runtime", "mode"))
def test_explicit_physical_or_runtime_counterfactual_keeps_original_prediction(retained_case, condition):
    if condition == "runtime":
        retained_case["runtime"]["vllm_version"] = "different-explicit-revision"
    elif condition == "mode":
        retained_case["machine"]["device"].setdefault("service_modes", {})[
            "reg_issue_slots"] = {"rate": 1.0}
    else:
        device = retained_case["machine"]["device"]
        field, key = ("rates", "hbm") if condition == "hbm" else ("compute_peaks", "bf16")
        device.setdefault(field, {})[key] = 1e6
    original = deepcopy(retained_case)
    result, provenance = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
    )
    assert provenance["status"] == "not_applicable"
    assert provenance["physical_contract_mismatches"]
    assert result == original == retained_case


def test_rule_guarded_owner_count_still_rejects_outside_its_domain(retained_case):
    # The retained profile's source_contract omits the default HBM owner count,
    # but every retained rule guards it; rule matching remains the second exact
    # gate and must not import a response under a different active owner count.
    retained_case["machine"]["device"].setdefault("resource_units", {})["hbm"] = 1
    original = deepcopy(retained_case)
    result, provenance = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
    )
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"] == "active_abi_or_declared_source_condition_outside_domain"
    assert provenance["unmatched_native_boundary"]
    assert result == original == retained_case


def test_additive_hardware_declarations_do_not_rewrite_the_retained_domain(retained_case):
    device = retained_case["machine"]["device"]
    device.setdefault("rates", {})["future_aiv_port"] = 1.0e12
    device.setdefault("resource_units", {})["future_aiv_port"] = 8
    device.setdefault("service_modes", {})["future_typed_call"] = {
        "resource": "future_aiv_port", "rate": 1.0e12,
    }
    original = deepcopy(retained_case)
    imported, provenance = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
    )
    assert provenance["status"] == "applied"
    assert len(provenance["matched_domains"]) == 5
    assert provenance["physical_contract_mismatches"] == []
    additions = provenance["undeclared_physical_contract_additions"]
    assert "devices.0.rates.future_aiv_port" in additions
    assert "devices.0.resource_units.future_aiv_port" in additions
    assert "devices.0.service_modes.future_typed_call" in additions
    assert provenance["consumption"] == "explicit_observation_replay"
    assert provenance["general_production_pricing"] is False
    assert imported != original and retained_case == original


def test_retained_declaration_cannot_disappear_from_the_current_environment(
        retained_case, tmp_path):
    profile = json.loads(PROFILE_PATH.read_text())
    profile["source_contract"]["devices"][0]["rates"]["retired_supply"] = 1.0
    path = tmp_path / "retained-with-retired-supply.json"
    path.write_text(json.dumps(profile))
    result, provenance = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
        profile_path=path,
    )
    assert provenance["status"] == "not_applicable"
    assert "devices.0.rates.retired_supply" in provenance["physical_contract_mismatches"]
    assert result == retained_case


def test_imported_rules_guard_only_declared_physical_leaves(retained_case):
    imported, _ = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
    )
    rules = [rule for rule in imported["runtime"]["kernels"]["service_regimes"]
             if rule["id"].startswith("a5-observed-native-")]
    assert len(rules) == 5
    for rule in rules:
        assert "physical_rates" not in rule["match"]
        assert "resource_units" not in rule["match"]
        assert "physical_rates.resources.hbm" in rule["match"]
        assert "physical_rates.resources.pipe_s_issue" not in rule["match"]
        assert "resource_units.vector" in rule["match"]
        assert rule["provenance"]["consumption"] == "explicit_observation_replay"
        assert rule["provenance"]["general_production_pricing"] is False
        assert rule["provenance"]["physical_guard_basis"] == "profile_declared_leaves"


def test_imported_rules_do_not_hide_a_later_physical_rate_change(retained_case):
    from mindie_sim import graph_costs, target_operators

    imported, _ = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
    )
    imported["machine"]["device"].setdefault("rates", {})["hbm"] = 1e6
    op = next(op for op in target_operators(
        imported, phase="decode", tokens=1, context=4096, sequences=4,
    ) if op.recipe == "linear_qkvz")
    report = graph_costs(imported, (op,), isolated=False,
                         external_inputs={dependency: 0 for dependency in op.deps})
    rules = [rule for rule in report["parameters"]["service_regimes"]
             if rule["id"].endswith("linear_qkvz-4x3072x2048")]
    assert rules and rules[0]["queries"] == {"physical_identity_mismatch": 1}
    assert "physical_rates.resources.hbm" in rules[0]["mismatched_axes"]


def test_imported_conv_response_cannot_cross_graph_padding_capacity(retained_case):
    from mindie_sim import graph_costs, target_operators

    imported, _ = apply_a5_native_observations(
        retained_case, phase="decode", tokens=1, context=4096, sequences=4,
    )
    imported["runtime"]["graph_capture_keys"] = [16]
    op = next(op for op in target_operators(
        imported, phase="decode", tokens=1, context=4096, sequences=4,
    ) if op.recipe == "ascend_causal_conv1d_update")
    assert op.local_shape[0] == 4 and op.padded_shape[0] == 16
    report = graph_costs(imported, (op,), isolated=False,
                         external_inputs={dependency: 0 for dependency in op.deps})
    rule = next(rule for rule in report["parameters"]["service_regimes"]
                if rule["id"].endswith("ascend_causal_conv1d_update-4x2048"))
    assert rule["queries"] == {"physical_identity_mismatch": 1}
    assert "metadata.graph_physical_query_rows" in rule["mismatched_axes"]
