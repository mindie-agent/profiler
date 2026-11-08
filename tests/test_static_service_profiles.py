"""Static native profiles are immutable, order-independent installations.

[Role] Verify static service profile immutability and order-independent installation.
[Invariants] Repeated or reordered profile installation produces identical predictions.
[Timeouts & Locks] Tier 0 (<5s), uses pytest tmp_path isolation.
[Side-Effect Policy] Writes only to isolated tmp_path.
"""
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples/structure"))

from a3_mla_native_observations import (  # noqa: E402
    PROFILE,
    STATIC_PROFILE,
    apply_a3_mla_native_observations,
    _load_profile,
)
from capture_policy import import_capture_policy  # noqa: E402
from mindie_sim import operator_costs, target_operators  # noqa: E402

FIXTURES = ROOT / "tests/fixtures/native_observations"
OUTPUT_A_RULE = "a3-sharedkv-output-a-native-m2-18"


def qualified_raw(tmp_path):
    """Build the captured shared-KV ABI through the real ingress path."""
    raw = json.loads((FIXTURES / "a3_dsv4f_mc2_padding.json").read_text())["raw"]
    with (FIXTURES / "a3_sharedkv_mla_abi.csv").open() as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    with (tmp_path / "kernel_details.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (tmp_path / "cmd.sh").write_bytes(
        (FIXTURES / "a3_dsv4f_mc2_cmd.sh").read_bytes())
    raw, provenance = import_capture_policy(
        raw, capture_path=tmp_path / "kernel_details.csv")
    assert provenance["mla_structure"]["status"] == "applied"
    return raw


def rule_ids(declaration):
    return [rule["id"] for rule in
            declaration["runtime"]["kernels"]["service_regimes"]]


def test_binder_is_idempotent_and_never_mutates_the_caller(tmp_path):
    raw = qualified_raw(tmp_path)
    before = deepcopy(raw)
    once, first = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    assert raw == before
    twice, second = apply_a3_mla_native_observations(
        once, phase="decode", tokens=2, context=4096, sequences=1)
    assert once == twice, "B(B(raw)) must equal B(raw)"
    assert second["status"] == "applied"
    assert second["reason"] == "static_physical_profile_already_installed"
    assert second["installed_rule_ids"] == []
    assert set(first["installed_rule_ids"]) == set(rule_ids(once))
    assert set(first["deduplicated_rule_ids"]) == set()
    assert set(second["deduplicated_rule_ids"]) == set(rule_ids(once))
    assert raw == before


def test_geometry_permutations_produce_one_identical_declaration(tmp_path):
    raw = qualified_raw(tmp_path)
    original = deepcopy(raw)
    geometries = [
        dict(phase="decode", tokens=1, context=4096, sequences=1),
        dict(phase="decode", tokens=2, context=0, sequences=4),
        dict(phase="decode", tokens=8, context=131072, sequences=32),
        dict(phase="prefill", tokens=8192, context=0, sequences=1),
        dict(phase="prefill", tokens=512, context=64512, sequences=1),
    ]
    declarations = [apply_a3_mla_native_observations(raw, **geometry)[0]
                    for geometry in geometries]
    assert raw == original
    assert all(declaration == declarations[0] for declaration in declarations)
    # A previously processed input is equivalent to a fresh one, including in
    # the reverse geometry order.
    processed = declarations[-1]
    repeated = apply_a3_mla_native_observations(
        processed, **geometries[0])[0]
    assert repeated == processed


def test_returned_declaration_is_a_private_copy_of_cached_profile_data(tmp_path):
    raw = qualified_raw(tmp_path)
    first, _ = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    first_rule = next(rule for rule in
                      first["runtime"]["kernels"]["service_regimes"]
                      if rule["id"] == OUTPUT_A_RULE)
    first_rule["response"]["fixed_us"] = -12345.0
    first_rule["match"]["recipe"] = "mutated_recipe"
    second, _ = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    restored = next(rule for rule in
                    second["runtime"]["kernels"]["service_regimes"]
                    if rule["id"] == OUTPUT_A_RULE)
    assert restored["response"]["fixed_us"] == pytest.approx(54.359)
    assert restored["match"]["recipe"] == "grouped_output_a"
    document, _ = _load_profile(PROFILE)
    document["rules"][0]["response"]["fixed_us"] = -1.0
    third, _ = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    cached = next(rule for rule in third["runtime"]["kernels"]["service_regimes"]
                  if rule["id"] == OUTPUT_A_RULE)
    assert cached["response"]["fixed_us"] == pytest.approx(54.359)


def test_empty_existing_rule_list_accepts_the_static_profile(tmp_path):
    raw = qualified_raw(tmp_path)
    raw["runtime"].setdefault("kernels", {})["service_regimes"] = []
    declared, provenance = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    assert provenance["status"] == "applied"
    assert OUTPUT_A_RULE in rule_ids(declared)


def test_edited_id_foreign_overlap_and_die_queue_conflict_preserve_input(tmp_path):
    raw = qualified_raw(tmp_path)
    edited = deepcopy(raw)
    edited["runtime"]["kernels"]["service_regimes"] = [{
        "id": OUTPUT_A_RULE,
        "match": {"phase": "decode", "recipe": "grouped_output_a"},
        "response": {"fixed_us": 123.0},
    }]
    before = deepcopy(edited)
    result, provenance = apply_a3_mla_native_observations(
        edited, phase="decode", tokens=2, context=4096, sequences=1)
    assert provenance["status"] == "conflict"
    assert provenance["reason"] == "existing_output_a_service_preserved"
    assert result == before

    foreign = deepcopy(raw)
    foreign["runtime"]["kernels"]["service_regimes"] = [{
        "id": "foreign-broad-gemm",
        "match": {"phase": "decode", "family": "gemm"},
        "response": {"fixed_us": 10.0},
    }]
    before = deepcopy(foreign)
    result, provenance = apply_a3_mla_native_observations(
        foreign, phase="decode", tokens=2, context=4096, sequences=1)
    assert provenance["status"] == "conflict"
    assert result == before

    queued = deepcopy(raw)
    queued["machine"]["dies"] = [
        {"rates": {"native_call_service": 500.0}}
        for _ in range(int(queued["machine"].get("num_devices", 8)))
    ]
    before = deepcopy(queued)
    result, provenance = apply_a3_mla_native_observations(
        queued, phase="decode", tokens=2, context=4096, sequences=1)
    assert provenance["status"] == "conflict"
    assert provenance["reason"] == "native_service_queue_conflicts_with_declaration"
    assert result == before


def test_m1_m19_install_the_rule_but_execute_the_analytical_path(tmp_path):
    raw = qualified_raw(tmp_path)
    for rows in (1, 19):
        declared, provenance = apply_a3_mla_native_observations(
            raw, phase="decode", tokens=rows, context=4096, sequences=1)
        assert provenance["status"] == "applied"
        assert OUTPUT_A_RULE in rule_ids(declared)
        op = next(op for op in target_operators(
            declared, phase="decode", tokens=rows, context=4096)
            if op.recipe == "grouped_output_a")
        priced = operator_costs(declared, (op,), input_ready_ms=7)["operators"][0]
        assert priced["program"] != "JointNativeService"
        assert priced["duration_ms"] != pytest.approx(.054359)
    inside, _ = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    op = next(op for op in target_operators(
        inside, phase="decode", tokens=2, context=4096)
        if op.recipe == "grouped_output_a")
    priced = operator_costs(inside, (op,), input_ready_ms=7)["operators"][0]
    assert priced["duration_ms"] == pytest.approx(.054359, rel=1e-6)


def test_static_declarations_use_physical_coordinates_not_outer_geometry(tmp_path):
    raw = qualified_raw(tmp_path)
    declared, _ = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1)
    forbidden = {"tokens", "context", "sequences", "layers", "model", "capture"}
    for rule in declared["runtime"]["kernels"]["service_regimes"]:
        assert not forbidden.intersection(rule.get("match", {}))
        assert "base_fixed_us" not in rule.get("provenance", {})
        assert "tokens" not in rule.get("id", "")
    static, identity = _load_profile(STATIC_PROFILE)
    assert identity["sha256"]
    assert static["groups"]
    for rule in [rule for group in static["groups"] for rule in group["rules"]]:
        assert rule.get("coordinates"), "every weighted rule declares a physical coordinate"
        assert set(rule["domain"]) <= set(rule["coordinates"])
        low = min(bounds["min"] for bounds in rule["domain"].values())
        high = max(bounds["max"] for bounds in rule["domain"].values())
        assert low <= high


def test_supersede_requires_an_explicit_owned_payload_hash(tmp_path):
    from a3_mla_native_observations import _rule_hash

    raw = qualified_raw(tmp_path)
    historical = {
        "id": OUTPUT_A_RULE,
        "match": {"phase": "decode", "recipe": "grouped_output_a"},
        "response": {"fixed_us": 50.0},
    }
    raw["runtime"]["kernels"]["service_regimes"] = [deepcopy(historical)]
    profile, _ = _load_profile(PROFILE)
    unowned = tmp_path / "unowned.json"
    unowned.write_text(json.dumps(profile))
    result, provenance = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1,
        profile_path=unowned)
    assert provenance["status"] == "conflict"
    assert result == raw

    owned_document = deepcopy(profile)
    owned_document["supersedes"] = {OUTPUT_A_RULE: [_rule_hash(historical)]}
    owned = tmp_path / "owned.json"
    owned.write_text(json.dumps(owned_document))
    declared, provenance = apply_a3_mla_native_observations(
        raw, phase="decode", tokens=2, context=4096, sequences=1,
        profile_path=owned)
    assert provenance["status"] == "applied"
    assert provenance["replaced_rule_payloads"] == [{
        "id": OUTPUT_A_RULE, "superseded_sha256": _rule_hash(historical)}]
    replacement = next(rule for rule in declared["runtime"]["kernels"]["service_regimes"]
                       if rule["id"] == OUTPUT_A_RULE)
    assert replacement["response"]["fixed_us"] == pytest.approx(54.359)

    scaled = deepcopy(raw)
    scaled["runtime"]["kernels"]["service_regimes"] = [{
        "id": "foreign-scaled-output-a",
        "match": {"phase": "decode", "recipe": "grouped_output_a"},
        "coordinates": {"m10": {"path": "local_shape.0", "scale": 10}},
        "domain": {"m10": {"min": 20, "max": 180}},
        "response": {"fixed_us": 42.0},
    }]
    before_scaled = deepcopy(scaled)
    res_scaled, prov_scaled = apply_a3_mla_native_observations(scaled)
    assert prov_scaled["status"] == "conflict"
    assert res_scaled == before_scaled

    edited_replaced = deepcopy(raw)
    edited_replaced["runtime"]["kernels"]["service_regimes"] = [
        {"id": "a3-v4flash-grouped-gate-up-c32", "match": {"recipe": "other"}, "response": {"fixed_us": 1.0}},
        {"id": "a3-retained-call-13d2f9a1640e2aa2", "match": {"recipe": "other2"}, "response": {"fixed_us": 1.0}},
        {"id": "a3-retained-call-8d059020c17f3e0d", "match": {"recipe": "edited"}, "response": {"fixed_us": 999.0}},
    ]
    before_edited = deepcopy(edited_replaced)
    res_edited, prov_edited = apply_a3_mla_native_observations(edited_replaced)
    assert prov_edited["status"] == "conflict"
    assert res_edited == before_edited
