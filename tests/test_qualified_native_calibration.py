"""Explicit qualified A2/A5 profiles bind only declared actual native ABI.

[Role] Verify real positives, queue reuse, no double charge and visible ABI
  failures on ordinary public Sim graphs.
[Invariants] Default replay is unchanged; a domain miss keeps the raw and an
  ordinary prediction reason; malformed/conflicting ABI raises a typed error.
[Timeouts & Locks] Small local CPU graphs and packaged JSON only; no NPU,
  network, timers, locks or capture reads.
[Side-Effect Policy] Read fixtures; runtime homes are isolated by conftest.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")
from mindie_sim import operator_costs, predict, target_operators
from mindie_sim.prediction.body_defaults import consume_target_declaration
from mindie_sim.prediction.call_gdn import make_call
from mindie_sim.prediction.graph_analysis import graph_costs
from mindie_sim.prediction.service_regimes import RegimePolicy
from mindie_sim.prediction.structure import parse_case

ROOT = Path(__file__).resolve().parents[1]
STRUCT = ROOT / "examples" / "structure"
FIXTURES = ROOT / "tests" / "fixtures" / "native_observations"
sys.path.insert(0, str(STRUCT))
from native_observations import (  # noqa: E402
    PROFILE_FILES, apply_native_observations, native_observation_identity,
    predict_body)
from qualified_native_calibration import (  # noqa: E402
    QualifiedAbiMismatch, QualifiedCalibrationIOError, apply_qualified_native_observations,
    load_qualified_profile, profile_names)


def _fixture(name):
    return json.loads((FIXTURES / name).read_text())


A2_CASE = _fixture("qualified_a2_case.json")
A2_ABI = _fixture("qualified_a2_abi.json")
A5_CASES = _fixture("qualified_a5_cases.json")
A5_ABI = _fixture("qualified_a5_abi.json")
A2_PROFILE = load_qualified_profile("a2-fia-dense")
A5_PROFILE = load_qualified_profile("a5-attention")


def _data(profile):
    return profile.data if hasattr(profile, "data") else profile


def _rule(profile, rule_id):
    data = _data(profile)
    return next(rule for rule in data["rules"] + data.get("train_only_rules", ())
                if rule["id"] == rule_id)


def _affine(rule, values):
    response = rule["response"]
    total = response.get("fixed_us", 0.0)
    for term in response.get("terms", ()):
        total += term["us_per_unit"] * values[term["coordinate"]]
    return total


def _response_values(rule, row):
    """Resolve only the projected ordinary-Sim coordinates the rule declares."""
    reference = row.get("analytical_reference_work") or {}
    operator = row["operator"]
    values = {}
    needed = {term["coordinate"] for term in rule["response"].get("terms", ())}
    for name, declaration in rule["coordinates"].items():
        if name not in needed:
            continue
        path = declaration["path"]
        if path == "work.hbm":
            value = reference["hbm"]
        elif path == "work.cube":
            value = reference["cube"]
        elif path.startswith("local_shape."):
            value = operator["local_shape"][int(path.rsplit(".", 1)[1])]
        elif path == "metadata.lengths":
            lengths = operator["metadata"]["lengths"]
            value = sum(lengths) if declaration.get("reduce") == "sum" else len(lengths)
        elif path == "metadata.gqa_prefill.requests":
            value = len(operator["metadata"]["gqa_prefill"]["requests"])
        else:  # pragma: no cover - catches an unintentional new projection
            raise AssertionError("unprojected coordinate: " + path)
        values[name] = value * declaration.get("scale", 1)
    return values


def _replace_rule(profile, rule_id):
    data = _data(profile)
    rule = deepcopy(_rule(data, rule_id))
    spec = data["projection"]["families"][rule["provenance"]["profile_family"]]
    for name, declaration in spec.get("coordinate_overrides", {}).items():
        rule["coordinates"][name] = deepcopy(declaration)
    return rule


def _joint_rows(applied, *, phase, tokens, context, recipes):
    operators = target_operators(applied, phase=phase, tokens=tokens,
                                 context=context, sequences=1)
    seen = set()
    selected = tuple(op for op in operators if op.recipe in recipes and not (op.recipe in seen or seen.add(op.recipe)))
    parsed = consume_target_declaration(parse_case(applied), selected)
    rows = operator_costs(parsed, selected, replay_scope="none")["operators"]
    return {row["operator"]["recipe"]: row for row in rows}


def test_profiles_preserve_frozen_rules_and_truthful_denominators():
    assert profile_names() == ("a2-fia-dense", "a5-attention")
    assert A2_PROFILE.data["schema"] == "mindie-profiler-qualified-native-calibration/1"
    assert A2_PROFILE.data["status"] == "qualified_experimental"
    assert A2_PROFILE.data["activation"] == "explicit_opt_in_named_profile_only"
    assert A2_PROFILE.data["families"] == ["fused_attention", "dense_matmul"]
    assert A2_PROFILE.data["train_only_families"] == ["gdn_gating"]
    a2_sources = A2_PROFILE.data["provenance"]["source_files"]
    assert a2_sources["native_adapter.py"]["sha256"] == (
        "ecf8d5bb57130a86e79f13e5af53e8b8acaa09df298024dff1098de2acbca54e")
    assert a2_sources["joint-service-arm.json"]["sha256"] == (
        "e9ac91391de3d4bcd43954ab11eb9b328f65e0fa0e66f29ad69d3cc94c0cf34f")
    assert a2_sources["frozen-regime-params.json"]["sha256"] == (
        "c72ea4a8a519cda9431888040089532ab3bbddc89acf601716c5de5db3db14f1")
    assert A2_PROFILE.data["provenance"]["source_rule_sha256"]["a2-fia-prefill-mask"] == (
        "9c1990f4f382b288939102f983f4ee97a8156d0a3827cc575aee872125ea9e49")
    assert [rule["id"] for rule in A2_PROFILE.data["rules"]] == [
        "a2-fia-decode-nomask-q1", "a2-fia-decode-mask-q8",
        "a2-fia-prefill-mask", "a2-w8a8-dense-kernel-v2"]
    assert [rule["id"] for rule in A2_PROFILE.data["train_only_rules"]] == [
        "a2-gating-kernel-v2"]
    fia = _rule(A2_PROFILE, "a2-fia-prefill-mask")
    assert fia["response"]["fixed_us"] == pytest.approx(26.83059574542758)
    assert {term["coordinate"]: term["us_per_unit"] for term in fia["response"]["terms"]} == {
        "work_hbm": pytest.approx(0.4495911143584332),
        "kv_rows": pytest.approx(10.621196528467568)}
    assert fia["domain"]["q"] == {"min": 64, "max": 2048}
    dense = _rule(A2_PROFILE, "a2-w8a8-dense-kernel-v2")
    assert dense["response"]["fixed_us"] == 0.0
    assert {term["coordinate"]: term["us_per_unit"] for term in dense["response"]["terms"]} == {
        "work_cube": pytest.approx(2.8583461604253246),
        "work_hbm": pytest.approx(0.8676450426650527),
        "m": pytest.approx(1.6748022638569409),
        "k": pytest.approx(5.561237464510273)}
    a2 = A2_PROFILE.data["provenance"]["denominators"]
    assert (a2["joint_calls"], a2["joint_within_10pct"], a2["joint_failures"]) == (114, 96, 18)
    assert a2["fia_analytical_domain_misses"] == 6
    assert a2["gdr_unsupported"] == 3
    assert a2["gating_heldout_rows"] == 0
    qualification = A2_PROFILE.data["provenance"]["qualification"]
    assert qualification["universal_per_call_10pct_gate"] is False
    assert qualification["gating_heldout_validated"] is False

    assert A5_PROFILE.data["families"] == [
        "attention_prefill_D128", "attention_prefill_D256", "ChunkFwdH"]
    assert [rule["id"] for rule in A5_PROFILE.data["rules"]] == [
        "a5-train85-attention_prefill_d128-8-1-128-prefill",
        "a5-train85-attention_prefill_d256-4-1-256-prefill",
        "a5-train85-attention_prefill_d256-3-1-256-prefill",
        "a5-train85-attention_prefill_d256-6-1-256-prefill",
        "a5-train85-chunkfwdh-4-8", "a5-train85-chunkfwdh-2-6",
        "a5-train85-chunkfwdh-4-12"]
    a5_sources = A5_PROFILE.data["provenance"]["source_files"]
    assert a5_sources["fit_v3.py"]["sha256"] == (
        "c5d2358bab16d8ef5adf3b78a5a50297674c696e26358223a7077828865715a9")
    assert a5_sources["v3_service_regimes.json"]["sha256"] == (
        "26988b1989cd37b7afd208963db0748f24e84c04f768bd570ce3c2df49e3af18")
    assert a5_sources["v3_frozen_family_parameters.json"]["sha256"] == (
        "94f2214f8ab18ee271ca147e3f47fd6f6e675594155df1b42f83ad80377d2992")
    assert A5_PROFILE.data["provenance"]["source_rule_sha256"][
        "a5-train85-chunkfwdh-4-8"] == (
        "e1867a47acfba3933707a07750661e6c07ad654a78c8883e22944bc311ebc9e9")
    assert not any("decode" in rule["id"] for rule in A5_PROFILE.data["rules"])
    assert not any("cast" in rule["id"] or "prepare" in rule["id"]
                   or "chunkfwdo" in rule["id"] for rule in A5_PROFILE.data["rules"])
    chunk = _rule(A5_PROFILE, "a5-train85-chunkfwdh-4-8")
    assert chunk["response"]["fixed_us"] == pytest.approx(1.9991305517710205)
    assert chunk["response"]["terms"] == [{
        "coordinate": "tokens", "us_per_unit": pytest.approx(0.048813473087329265)}]
    assert chunk["domain"] == {"tokens": {"min": 2048.0, "max": 32768.0},
                               "batch": {"min": 1.0, "max": 1.0}}
    a5 = A5_PROFILE.data["provenance"]["denominators"]
    assert (a5["priority_domain_points"], a5["priority_domain_points_pass"]) == (8, 8)
    assert (a5["chunked_attention_bound_points"], a5["chunk_fwd_h_T12288_bound_points"]) == (5, 3)
    assert a5["pure_prefill_1536_65536"] == "predeclared_outside_domain"
    assert (a5["whole_a5_rows"], a5["whole_a5_joint_rows"],
            a5["whole_a5_fallback_rows"], a5["whole_a5_joint_within_10pct"]) == (87, 54, 33, 37)
    assert a5["whole_a5_weighted_absolute_relative"] == pytest.approx(0.6100263465228096)
    assert A5_PROFILE.data["provenance"]["qualification"]["whole_a5_pass"] is False
    assert A5_PROFILE.data["provenance"]["qualification"][
        "attention_decode_D256_promoted"] is False
    for profile in (A2_PROFILE, A5_PROFILE):
        RegimePolicy(profile.data["rules"])


def test_default_arm_does_not_import_the_qualified_profiles():
    raw = deepcopy(A2_CASE)
    original = deepcopy(raw)
    selected, provenance = apply_native_observations(
        raw, phase="prefill", tokens=2048, context=0)
    assert selected == raw == original
    assert provenance["qualified_profiles"] == []
    assert not any(rule["id"].startswith("a2-fia-") or rule["id"].startswith("a2-w8a8-")
                   for rule in selected["runtime"]["kernels"].get("service_regimes", []))

    applied, provenance = apply_native_observations(
        raw, phase="prefill", tokens=2048, context=0,
        qualified=(("a2-fia-dense", A2_ABI["prefill"]),))
    assert raw == original
    assert provenance["qualified_profiles"][0]["status"] == "applied"
    rules = applied["runtime"]["kernels"]["service_regimes"]
    assert any(rule["id"] == "a2-fia-prefill-mask" for rule in rules)
    assert any(rule["id"].startswith("a2-w8a8-dense-kernel-v2.") for rule in rules)


def test_train_only_gating_is_recorded_without_a_heldout_claim():
    default, _ = apply_qualified_native_observations(
        deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill", tokens=2048,
        context=0, native_abi=A2_ABI["prefill"])
    assert not any(rule["id"] == "a2-gating-kernel-v2"
                   for rule in default["runtime"]["kernels"]["service_regimes"])
    applied, provenance = apply_qualified_native_observations(
        deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill", tokens=2048,
        context=0, native_abi=A2_ABI["prefill"], include_train_only=True)
    assert provenance["status"] == "applied"
    assert provenance["train_only_families_applied"] == []
    assert provenance["heldout_validated"] is False
    assert any(rule["id"] == "a2-gating-kernel-v2"
               for rule in applied["runtime"]["kernels"]["service_regimes"])
    assert not any(row["profile_family"] == "gdn_gating"
                   for row in provenance["matched_boundaries"])


def test_a2_real_positive_fia_and_dense_share_one_queue_without_double_charge():
    raw = deepcopy(A2_CASE)
    original = deepcopy(raw)
    applied, provenance = apply_qualified_native_observations(
        raw, profile="a2-fia-dense", phase="prefill", tokens=2048, context=0,
        native_abi=A2_ABI["prefill"])
    assert raw == original
    assert provenance["status"] == "applied"
    assert provenance["reason"] == "actual_native_abi_and_boundaries_within_qualified_domain"
    assert provenance["heldout_evaluated"] is True
    assert provenance["heldout_validated"] is False
    assert provenance["heldout_status"] == "heldout_accounted_not_universal_10pct"
    assert provenance["queue"]["resource"] == "qualified_native_service"
    families = {row["profile_family"] for row in provenance["matched_boundaries"]}
    assert families == {"fused_attention", "dense_matmul"}
    imported = applied["runtime"]["kernels"]["service_regimes"]
    assert imported and all(rule["execution"]["resource"] == "qualified_native_service"
                             for rule in imported)
    assert applied["machine"]["device"]["rates"]["qualified_native_service"] == 1e9
    assert applied["machine"]["device"]["resource_units"]["qualified_native_service"] == 1
    assert applied["machine"]["device"]["work_units"]["qualified_native_service"] == "busy_ns"

    rows = _joint_rows(applied, phase="prefill", tokens=2048, context=0,
                       recipes={"flash_attention_prefill", "dense_gate_up"})
    attention = rows["flash_attention_prefill"]
    dense = rows["dense_gate_up"]
    assert attention["program"] == dense["program"] == "JointNativeService"
    fia_rule = _replace_rule(A2_PROFILE.data, "a2-fia-prefill-mask")
    assert attention["duration_ms"] * 1000 == pytest.approx(
        _affine(fia_rule, _response_values(fia_rule, attention)))
    dense_rule = _replace_rule(A2_PROFILE.data, "a2-w8a8-dense-kernel-v2")
    assert dense["duration_ms"] * 1000 == pytest.approx(
        _affine(dense_rule, _response_values(dense_rule, dense)))
    for row in (attention, dense):
        assert row["analytical_reference_work"]
        assert row["joint_native_service"]["resource"] == "qualified_native_service"
    repeated, again = apply_qualified_native_observations(
        applied, profile="a2-fia-dense", phase="prefill", tokens=2048, context=0,
        native_abi=A2_ABI["prefill"])
    assert repeated == applied
    assert again["status"] == "applied"


@pytest.mark.parametrize("abi_key,tokens,rule_id", (
    ("q1", 1, "a2-fia-decode-nomask-q1"),
    ("q8", 8, "a2-fia-decode-mask-q8"),
))
def test_a2_decode_mask_domains_select_their_frozen_rule(abi_key, tokens, rule_id):
    applied, provenance = apply_qualified_native_observations(
        deepcopy(A2_CASE), profile="a2-fia-dense", phase="decode",
        tokens=tokens, context=8192, native_abi=A2_ABI[abi_key])
    assert provenance["status"] == "applied"
    source_ids = {row["source_rule_id"] for row in provenance["matched_boundaries"]}
    assert rule_id in source_ids
    rows = _joint_rows(applied, phase="decode", tokens=tokens, context=8192,
                       recipes={"flash_attention_decode"})
    assert rows["flash_attention_decode"]["program"] == "JointNativeService"

    with pytest.raises(QualifiedAbiMismatch):
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="decode",
            tokens=tokens, context=8192,
            native_abi=A2_ABI["q8" if abi_key == "q1" else "q1"])


def test_predict_body_qualified_arm_executes_the_shared_joint_queue():
    raw = deepcopy(A2_CASE)
    prediction = predict_body(
        raw, phase="decode", tokens=1, context=8192, sequences=1,
        qualified=(("a2-fia-dense", A2_ABI["q1"]),))
    applied = prediction["native_observation_provenance"]["qualified_profiles"]
    assert [row["status"] for row in applied] == ["applied"]
    services = prediction["parameters"]["joint_native_services"]
    assert services and all(row["resource"] == "qualified_native_service"
                             for row in services)
    assert all(row["replaced_primitive_count"] == 0 for row in services)
    assert all(row["analytical_reference_work"] for row in services)


def test_explicit_caller_paged_view_is_not_overwritten_by_profile_labels():
    operators = target_operators(A2_CASE, phase="prefill", tokens=2048, context=0)
    attention = next(op for op in operators if op.recipe == "flash_attention_prefill")
    metadata = dict(attention.metadata)
    metadata["attention_tensor_view"] = {
        **dict(metadata["attention_tensor_view"]), "kv_storage": "paged",
        "kind": "paged", "paged": True,
    }
    changed = replace(attention, metadata=tuple(metadata.items()))
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
            tokens=2048, context=0, operators=(changed,),
            native_abi={"fused_attention": A2_ABI["prefill"]["fused_attention"]})
    assert error.value.code == "native_abi_caller_view_incompatible"

    changed = replace(attention, layout="FRACTAL_NZ")
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
            tokens=2048, context=0, operators=(changed,),
            native_abi={"fused_attention": A2_ABI["prefill"]["fused_attention"]})
    assert error.value.code == "native_abi_caller_layout_incompatible"

    dense = next(op for op in operators if op.recipe == "dense_gate_up")
    metadata = dict(dense.metadata)
    metadata["int8_weight_metadata"] = "scale_offset"
    changed = replace(dense, metadata=tuple(metadata.items()))
    missed, provenance = apply_qualified_native_observations(
        deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
        tokens=2048, context=0, operators=(changed,),
        native_abi={"dense_matmul": A2_ABI["prefill"]["dense_matmul"]})
    assert missed == A2_CASE
    assert provenance["reason"] == "qualified_native_boundary_outside_domain"
    assert provenance["unmatched_boundaries"][0]["recipe"] == "dense_gate_up"


@pytest.mark.parametrize("mutate,code", [
    (lambda abi: abi["fused_attention"]["input_dtypes"].__setitem__(0, "DT_FP16"),
     "native_abi_input_contract_mismatch"),
    (lambda abi: abi["fused_attention"]["kv_view"].update(
        {"kind": "paged", "kv_storage": "paged", "paged": True}),
     "native_abi_field_mismatch"),
    (lambda abi: abi["fused_attention"]["geometry"].__setitem__("query_heads", 5),
     "native_abi_geometry_mismatch"),
    (lambda abi: abi["fused_attention"]["control_flags"].__setitem__("mask", "none"),
     "native_abi_mask_mismatch"),
])
def test_a2_actual_abi_conflicts_are_typed_visible_errors(mutate, code):
    abi = deepcopy(A2_ABI["prefill"])
    mutate(abi)
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
            tokens=2048, context=0, native_abi=abi)
    assert error.value.code == code


def test_a2_missing_abi_and_domain_or_queue_miss_keep_ordinary_prediction():
    with pytest.raises(QualifiedAbiMismatch, match="actual_native_abi_not_declared"):
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
            tokens=2048, context=0, native_abi=None)

    raw = deepcopy(A2_CASE)
    original = deepcopy(raw)
    missed, provenance = apply_qualified_native_observations(
        raw, profile="a2-fia-dense", phase="prefill", tokens=4096, context=0,
        native_abi=A2_ABI["prefill"])
    assert missed == raw == original
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"] == "qualified_native_boundary_outside_domain"
    assert provenance["unmatched_boundaries"][0]["local_shape"] == [4096, 4096, 6, 256]

    missed_decode, provenance = apply_qualified_native_observations(
        deepcopy(A2_CASE), profile="a2-fia-dense", phase="decode", tokens=16,
        context=8192, native_abi=A2_ABI["q8"])
    assert provenance["reason"] == "qualified_native_boundary_outside_domain"
    ordinary = predict(missed_decode, scope="body", phase="decode", tokens=16,
                       context=8192, sequences=1, event_limit=0)
    assert ordinary["status"] == "modeled" and ordinary["body_forward_ms"] > 0

    changed = deepcopy(A2_CASE)
    changed["model"]["quant"]["int8_weight_metadata"] = "scale_offset"
    missed, provenance = apply_qualified_native_observations(
        changed, profile="a2-fia-dense", phase="prefill", tokens=2048, context=0,
        native_abi=A2_ABI["prefill"])
    assert missed == changed
    assert provenance["reason"] == "quantization_outside_qualified_domain"

    changed = deepcopy(A2_CASE)
    changed["machine"]["device"] = {"rates": {"qualified_native_service": 2e9}}
    missed, provenance = apply_qualified_native_observations(
        changed, profile="a2-fia-dense", phase="prefill", tokens=2048, context=0,
        native_abi=A2_ABI["prefill"])
    assert missed == changed
    assert provenance["reason"] == "qualified_queue_declaration_conflict"


def test_a5_real_positive_three_families_and_heldout_geometries():
    expectations = {
        "qwen35_tp4_h4": ("attention_prefill_D256",
                          "a5-train85-attention_prefill_d256-4-1-256-prefill"),
        "qwen30_tp4_h8": ("attention_prefill_D128",
                          "a5-train85-attention_prefill_d128-8-1-128-prefill"),
        "qwen36_tp4_h6": ("attention_prefill_D256",
                          "a5-train85-attention_prefill_d256-6-1-256-prefill"),
        "qwen36_tp8_h3": ("attention_prefill_D256",
                          "a5-train85-attention_prefill_d256-3-1-256-prefill"),
    }
    for case_name, (family, rule_id) in expectations.items():
        raw = deepcopy(A5_CASES[case_name])
        original = deepcopy(raw)
        applied, provenance = apply_qualified_native_observations(
            raw, profile="a5-attention", phase="prefill", tokens=8192,
            context=24576, native_abi=A5_ABI[case_name])
        assert raw == original
        assert provenance["status"] == "applied"
        assert provenance["matched_boundaries"][0]["profile_family"] == family
        assert provenance["matched_boundaries"][0]["source_rule_id"] == rule_id
        assert provenance["queue"]["resource"] == "native_local_service"
        assert provenance["heldout_evaluated"] is True
        assert provenance["heldout_validated"] is False
        assert provenance["heldout_status"] == "priority_domain_heldout_pass_not_whole_profile"
        row = _joint_rows(applied, phase="prefill", tokens=8192, context=24576,
                          recipes={"flash_attention_prefill"})["flash_attention_prefill"]
        assert row["program"] == "JointNativeService"
        rule = _rule(A5_PROFILE.data, rule_id)
        assert row["duration_ms"] * 1000 == pytest.approx(
            _affine(rule, _response_values(rule, row)))
        assert row["analytical_reference_work"]
        assert row["joint_native_service"]["resource"] == "native_local_service"

    for case_name, heads, keys, rule_id in (
            ("chunk_h8", 8, 4, "a5-train85-chunkfwdh-4-8"),
            ("chunk_h6", 6, 2, "a5-train85-chunkfwdh-2-6"),
            ("chunk_h12", 12, 4, "a5-train85-chunkfwdh-4-12")):
        raw = deepcopy(A5_CASES["qwen35_tp4_h4"])
        call = make_call("scan_prefill", dict(batch=1, tokens=12288, k_heads=keys,
                                              v_heads=heads, k_dim=128, v_dim=128,
                                              chunk=64))
        applied, provenance = apply_qualified_native_observations(
            raw, profile="a5-attention", phase="prefill", tokens=12288,
            context=0, native_abi=A5_ABI[case_name],
            operators=call.ops, recipes=call.recipes)
        assert provenance["status"] == "applied"
        assert [row["source_rule_id"] for row in provenance["matched_boundaries"]] == [rule_id]
        assert provenance["operator_source"] == "caller_declared_public_call"
        report = graph_costs(applied, call.ops, recipes=call.recipes)
        row = next(row for row in report["isolated"]["operators"]
                   if row["operator"]["recipe"] == "chunk_fwd_h")
        assert row["program"] == "JointNativeService"
        rule = _rule(A5_PROFILE.data, rule_id)
        assert row["duration_ms"] * 1000 == pytest.approx(
            _affine(rule, _response_values(rule, row)))
        assert row["analytical_reference_work"]
        assert report["parameters"]["joint_native_services"][0]["replaced_primitive_count"] == 0


def test_a5_abi_and_predeclared_domain_misses_are_distinct():
    abi = deepcopy(A5_ABI["qwen35_tp4_h4"])
    abi["attention_prefill_D256"]["geometry"]["head_dim"] = 128
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A5_CASES["qwen35_tp4_h4"]), profile="a5-attention",
            phase="prefill", tokens=8192, context=24576, native_abi=abi)
    assert error.value.code == "native_abi_geometry_mismatch"

    abi = deepcopy(A5_ABI["qwen35_tp4_h4"])
    abi["attention_prefill_D256"]["kv_view"].update(
        {"kind": "paged", "kv_storage": "paged", "paged": True})
    with pytest.raises(QualifiedAbiMismatch, match="native_abi_field_mismatch"):
        apply_qualified_native_observations(
            deepcopy(A5_CASES["qwen35_tp4_h4"]), profile="a5-attention",
            phase="prefill", tokens=8192, context=24576, native_abi=abi)

    for tokens, context, case_name in ((1536, 0, "qwen35_tp4_h4"),
                                       (8192, 0, "qwen30_tp4_h8")):
        abi = deepcopy(A5_ABI[case_name])
        key = "attention_prefill_D128" if case_name == "qwen30_tp4_h8" else "attention_prefill_D256"
        q = tokens
        kv = q + context
        abi[key]["input_shapes"][:3] = [f"{q},{abi[key]['geometry']['query_heads']},"
                                        f"{abi[key]['geometry']['head_dim']}",
                                        f"{kv},1,{abi[key]['geometry']['head_dim']}",
                                        f"{kv},1,{abi[key]['geometry']['head_dim']}"]
        abi[key]["output_shapes"] = [abi[key]["input_shapes"][0]]
        missed, provenance = apply_qualified_native_observations(
            deepcopy(A5_CASES[case_name]), profile="a5-attention", phase="prefill",
            tokens=tokens, context=context, native_abi=abi)
        assert missed == A5_CASES[case_name]
        assert provenance["status"] == "not_applicable"
        assert provenance["reason"] == "qualified_native_boundary_outside_domain"

    missed, provenance = apply_qualified_native_observations(
        deepcopy(A5_CASES["qwen35_tp4_h4"]), profile="a5-attention",
        phase="decode", tokens=1, context=8192,
        native_abi={"attention_prefill_D256": A5_ABI["qwen35_tp4_h4"][
            "attention_prefill_D256"]})
    assert missed == A5_CASES["qwen35_tp4_h4"]
    assert provenance["reason"] == "qualified_native_boundary_not_present"


@pytest.mark.parametrize("field,value,code", (
    ("output_dtypes", ["FLOAT", "FLOAT"], "native_abi_input_contract_mismatch"),
    ("output_formats", ["FRACTAL_NZ", "ND"], "native_abi_input_contract_mismatch"),
    ("input_formats", ["FRACTAL_NZ"] * 31, "native_abi_input_contract_mismatch"),
    ("output_shapes", [], "native_abi_slots_incomplete"),
))
def test_a5_attention_complete_slots_reject_conflicts_and_missing_outputs(field, value, code):
    abi = deepcopy(A5_ABI["qwen35_tp4_h4"])
    abi["attention_prefill_D256"][field] = value
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A5_CASES["qwen35_tp4_h4"]), profile="a5-attention",
            phase="prefill", tokens=8192, context=24576, native_abi=abi)
    assert error.value.code == code


@pytest.mark.parametrize("field,value,code", (
    ("output_dtypes", ["FLOAT", "DT_BF16", "DT_BF16"],
     "native_abi_input_contract_mismatch"),
    ("output_formats", ["ND", "ND", "FRACTAL_NZ"],
     "native_abi_input_contract_mismatch"),
    ("output_shapes", ["1", "1,8,12288,128", "131072"],
     "native_abi_geometry_mismatch"),
    ("input_formats", ["FRACTAL_NZ"] * 7, "native_abi_input_contract_mismatch"),
    ("input_shapes", ["1,4,12288,128", "1,8,12288,128", "1", "1,8,12288",
                      "1,8,128,128", "2", "384"], "native_abi_geometry_mismatch"),
))
def test_a5_chunk_complete_slots_reject_output_and_active_slot_conflicts(field, value, code):
    call = make_call("scan_prefill", dict(batch=1, tokens=12288, k_heads=4,
                                          v_heads=8, k_dim=128, v_dim=128, chunk=64))
    abi = deepcopy(A5_ABI["chunk_h8"])
    abi["ChunkFwdH"][field] = value
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A5_CASES["qwen35_tp4_h4"]), profile="a5-attention",
            phase="prefill", tokens=12288, context=0, native_abi=abi,
            operators=call.ops, recipes=call.recipes)
    assert error.value.code == code


@pytest.mark.parametrize("field,value", (
    ("output_dtype", "float32"), ("key_dtype", "float16"),
    ("query_shape", [1]), ("logical_layout", "paged"),
))
def test_explicit_caller_view_dtypes_and_shapes_are_reconciled(field, value):
    operators = target_operators(A2_CASE, phase="prefill", tokens=2048, context=0)
    attention = next(op for op in operators if op.recipe == "flash_attention_prefill")
    metadata = dict(attention.metadata)
    metadata["attention_tensor_view"] = {
        **dict(metadata["attention_tensor_view"]), field: value,
    }
    changed = replace(attention, metadata=tuple(metadata.items()))
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
            tokens=2048, context=0, operators=(changed,),
            native_abi={"fused_attention": A2_ABI["prefill"]["fused_attention"]})
    assert error.value.code == "native_abi_caller_view_incompatible"


def test_explicit_caller_service_identity_paged_is_reconciled():
    operators = target_operators(A2_CASE, phase="prefill", tokens=2048, context=0)
    attention = next(op for op in operators if op.recipe == "flash_attention_prefill")
    metadata = dict(attention.metadata)
    metadata["implementation"] = {"kv_storage": "paged"}
    changed = replace(attention, metadata=tuple(metadata.items()))
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
            tokens=2048, context=0, operators=(changed,),
            native_abi={"fused_attention": A2_ABI["prefill"]["fused_attention"]})
    assert error.value.code == "native_abi_caller_service_identity_incompatible"


def test_original_nested_service_identity_paged_is_reconciled():
    operators = target_operators(A2_CASE, phase="prefill", tokens=2048, context=0)
    attention = next(op for op in operators if op.recipe == "flash_attention_prefill")
    metadata = dict(attention.metadata)
    metadata["service_identity"] = {
        "implementation": {"kv_storage": "paged", "paged": True}}
    changed = replace(attention, metadata=tuple(metadata.items()))
    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A2_CASE), profile="a2-fia-dense", phase="prefill",
            tokens=2048, context=0, operators=(changed,),
            native_abi={"fused_attention": A2_ABI["prefill"]["fused_attention"]})
    assert error.value.code == "native_abi_caller_service_identity_incompatible"


def test_a5_true_train_total_kv_and_wrong_context_through_public_engine():
    raw = deepcopy(A5_CASES["qwen35_tp4_h4"])
    applied, provenance = apply_qualified_native_observations(
        raw, profile="a5-attention", phase="prefill", tokens=8192,
        context=24576, native_abi=A5_ABI["qwen35_tp4_h4"])
    assert provenance["status"] == "applied"
    assert provenance["matched_boundaries"][0]["local_shape"] == [8192, 32768, 4, 256]
    row = _joint_rows(applied, phase="prefill", tokens=8192, context=24576,
                      recipes={"flash_attention_prefill"})["flash_attention_prefill"]
    assert row["program"] == "JointNativeService"
    assert row["operator"]["local_shape"] == [8192, 32768, 4, 256]
    assert row["analytical_reference_work"]["cube"] == pytest.approx(962089451520.0)
    rule = _rule(A5_PROFILE.data, "a5-train85-attention_prefill_d256-4-1-256-prefill")
    assert row["duration_ms"] * 1000 == pytest.approx(3484.5328946101044)
    assert row["duration_ms"] * 1000 == pytest.approx(
        _affine(rule, _response_values(rule, row)))

    with pytest.raises(QualifiedAbiMismatch) as error:
        apply_qualified_native_observations(
            deepcopy(A5_CASES["qwen35_tp4_h4"]), profile="a5-attention",
            phase="prefill", tokens=8192, context=32768,
            native_abi=A5_ABI["qwen35_tp4_h4"])
    assert error.value.code == "native_abi_geometry_mismatch"


def test_qualified_request_with_prepared_scope_is_rejected_visibly():
    class Scope:
        def apply(self, *args, **kwargs):
            raise AssertionError("scope must not be entered")

    with pytest.raises(ValueError, match="qualified_profiles_not_supported_with_prepared_scope"):
        predict_body(deepcopy(A2_CASE), phase="prefill", tokens=2048, context=0,
                     scope=Scope(), qualified=(("a2-fia-dense", A2_ABI["prefill"]),))


@pytest.mark.parametrize("relative", (
    "qualified_native_calibration.py", "qualified_native_abi.py",
    "profiles/a2_fia_dense_qualified_20261107.json",
    "profiles/a5_attention_qualified_20261107.json",
))
def test_qualified_helper_and_profiles_participate_in_cache_identity(tmp_path, relative):
    assert relative in PROFILE_FILES
    source = STRUCT
    for name in PROFILE_FILES:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((source / name).read_bytes())
    before = native_observation_identity(tmp_path)
    changed = tmp_path / relative
    changed.write_bytes(changed.read_bytes() + b"\n")
    after = native_observation_identity(tmp_path)
    assert before != after


def test_bad_profile_path_is_a_typed_io_error():
    with pytest.raises(QualifiedCalibrationIOError):
        load_qualified_profile(str(FIXTURES / "does-not-exist.json"))
