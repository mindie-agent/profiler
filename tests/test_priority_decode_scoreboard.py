"""Cross-check prioritization against recorded cohort activity arithmetic."""
import importlib
import hashlib
import json
from pathlib import Path

import pytest


def test_failed_extraction_reads_remain_visible_without_adding_zero_populations(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    source = root / "examples/structure/acceptance-20261030-runtime67/decode-forward-v4_kimi-replay.json"
    if not source.exists():
        pytest.skip("retained runtime matrix is required for this failure regression")
    report = module.build([source], [])
    assert report["summary"]["body_failed_attempts"] == 3
    assert report["summary"]["unique_source_count"] == 29
    assert all(row["comparison"]["observed_ms"]["count"] > 0 for row in report["current_body_comparisons"])
    assert all(row["error"]["message"] == "declared_forward_extraction_missing"
               for row in report["body_failed_attempts"])


def test_invalid_quantization_receipt_retains_real_population_but_loses_accuracy(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    base = root / "examples/structure/acceptance-20261030-kimi-variants"
    path = base / "decode-forward-09811dad-replay.json"
    report = module.build([path], [], invalidation_paths=[base / "prediction-input-binding-invalidation.json"])
    assert report["summary"]["current_body_compared"] == 0
    assert report["summary"]["body_passed"] == 0
    assert report["summary"]["unique_observed_forward_count"] == 1799
    assert all(row["comparison"]["predicted_ms"] is None for row in report["body_comparisons"])
    assert sum(row["original_comparison"].get("passed") is True
               for row in report["body_comparisons"]) == 5
    corrected = base / "decode-forward-332f0420-window8-replay.json"
    after = module.build([path, corrected], [], invalidation_paths=[base / "prediction-input-binding-invalidation.json"])
    assert after["summary"]["unique_observed_forward_count"] == 1799
    assert after["summary"]["current_body_compared"] == 17
    assert after["summary"]["current_body_passed"] == 1
    # History references preserve all original layer detail while the selected
    # current arm retains an expanded table for the report's layer comparison.
    sources = {str(item.resolve()): json.loads(item.read_text()) for item in (path, corrected)}
    for row in after["body_comparisons"]:
        case = next(item for item in sources[row["receipt"]["path"]]["cases"]
                    if item["case_id"] == row["case_id"])
        layers = case.get("per_layer_comparison") or {}
        assert row["per_layer_reference"]["sha256"] == hashlib.sha256(
            json.dumps(layers, sort_keys=True).encode()).hexdigest()
    assert all("per_layer" in row for row in after["current_body_comparisons"])


def test_prediction_timeout_keeps_completed_capture_population(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    source = root / "examples/structure/acceptance-20261030-matrix-fix/decode-forward-glm-replay.json"
    report = module.build([source], [])
    failure, = report["body_failed_attempts"]
    assert failure["comparison"]["observed_ms"]["count"] == 27
    assert failure["prediction_failure"]["reason"] == "body_prediction_timeout"
    assert report["summary"]["unique_source_count"] == 26
    assert report["summary"]["current_body_compared"] == 25
    assert report["summary"]["latest_body_attempt_count"] == 26
    assert report["summary"]["latest_body_attempt_failed"] == 1


def test_real_cohort_priority_uses_complete_forward_and_per_call_tier(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    source = root / "examples/structure/acceptance-20261030-high-concurrency/body-operator-family-scoreboard.json"
    if not source.exists():
        pytest.skip("recorded acceptance campaign is available in the source checkout")
    receipt = json.loads(source.read_text())
    families, rows = module.operator_rows(receipt, {"path": str(source)})
    original = {(case["case_id"], cohort["cohort_id"]): (case["forward_count"], cohort)
                for case in receipt["cases"] for family in case["families"]
                for cohort in family["cohorts"] if cohort["status"] == "compared"}
    assert len(rows) == len(original) == 168
    for row in rows:
        forwards, cohort = original[row["case_id"], row["cohort_id"]]
        activity = cohort["comparison"]["activity_sum"]["signed_residual_ms"]
        assert row["signed_activity_residual_ms_per_forward"] == pytest.approx(activity / forwards)
        assert row["heavy_call"] == (cohort["observed"]["duration_ns"]["mean"] > 50_000)
    unscored = [row for row in families if row["unscored_event_count"]]
    assert unscored and all(not row["missing_match_is_missing_cost"] for row in unscored)
    # Large cumulative micro-kernel activity must not be promoted into >50us.
    assert any(row["measured_activity_ms_per_forward"] > 1 and not row["heavy_call"] for row in rows)


def test_runtime_controls_replace_current_prediction_without_duplicating_real_forwards(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    base = root / "examples/structure/acceptance-20261030-priority"
    old = base / "decode-forward-second-wave-replay.json"
    update = base / "decode-forward-glm-runtime-controls-replay.json"
    before = module.build([old], [])
    after = module.build([old, update], [])
    cases = {row["case_id"]: row for row in after["current_body_comparisons"]}
    b8 = next(row for key, row in cases.items() if key.startswith("a3_glm53_dc4k_b8")
              and row["comparison"]["status"] == "compared")
    assert b8["comparison"]["passed"]
    assert b8["comparison"]["predicted_ms"] == pytest.approx(44.050191, abs=1e-6)
    # Runtime controls include three genuinely different GLM45 sources as well
    # as two repeated GLM78 populations. Only the three new sources add samples.
    originals = {row["source_identity"]["sha256"] for row in before["body_comparisons"]}
    new = module.build([update], [])
    new_populations = [row for row in new["current_body_comparisons"]
                       if row["source_identity"]["sha256"] not in originals]
    assert after["summary"]["unique_observed_forward_count"] == (
        before["summary"]["unique_observed_forward_count"]
        + sum(row["comparison"]["observed_ms"]["count"] for row in new_populations))


@pytest.mark.parametrize("generic_schema", [False, True])
def test_full_native_reference_groups_survive_operator_selection_without_scoring(monkeypatch, tmp_path, generic_schema):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    reviewer = importlib.import_module("review_priority_decode_scoreboard")
    base = root / "examples/structure"
    operators = [base / "acceptance-20261030-matrix-fix" / name / "body-operator-family-scoreboard.json"
                 for name in ("glm-operators-86c1ee8f", "glm-low-concurrency-86c1ee8f")]
    refs = base / "acceptance-20261030-glm-native-references-c2261d63/glm-native-reference-scoreboard.json"
    if generic_schema:
        retained = json.loads(refs.read_text())
        retained["schema_version"] = "mindie-native-body-reference-batch/1"
        refs = tmp_path / "generic-native-references.json"
        refs.write_text(json.dumps(retained))
    before = module.build([], operators)
    after = module.build([], operators, [refs])
    assert after["current_operator_cohorts"] == before["current_operator_cohorts"]
    assert after["summary"]["operator_accuracy_by_tier"] == before["summary"]["operator_accuracy_by_tier"]
    assert after["summary"]["current_operator_scored_events"] == before["summary"]["current_operator_scored_events"]
    native = [row for row in after["current_source_role_references"]
              if row.get("reference_origin") == "external_native_partition"]
    assert len(native) == 36
    assert after["summary"]["current_external_native_reference_calls"] == 27666
    assert after["summary"]["current_external_native_reference_forwards"] == 318
    originals = {(case["case_id"], group["group_id"]): group
                 for case in json.loads(refs.read_text())["cases"] for group in case["groups"]}
    populations = {module._population(row) for row in after["current_operator_families"]}
    for row in native:
        assert module._population(row) in populations
        original = originals[row["case_id"], row["group_id"]]
        assert row["observed_us"] == original["observed_us"]
        assert row["layer_ids"] == original["layer_ids"]
        assert not row["scored"] and not row["additional_budget_allowed"]
        assert row["status"] == "reference_only"
    output = tmp_path / "native-reference-scoreboard.json"
    output.write_text(json.dumps(after))
    review = reviewer.review(output)
    assert review["status"] == "passed", review["failures"]


def test_native_selection_retains_distinct_observed_abis_and_latest_program(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    source = root / "examples/structure/acceptance-20261030-glm-native-references-c2261d63/glm-native-reference-scoreboard.json"
    cases = json.loads(source.read_text())["cases"]
    c1 = next(case for case in cases if case["case_id"] == "glm53flash-a5-tp8-c1")
    c64 = next(case for case in cases if case["case_id"] == "a5_glm53flash_tp8_c64_p4k")
    one = module.native_reference_rows(c1, {"path": "first", "sha256": "first"})[0]
    larger = module.native_reference_rows(c64, {"path": "second", "sha256": "second"})[0]
    assert one["native_operator_type"] == larger["native_operator_type"]
    assert one["layer_ids"] == larger["layer_ids"]
    assert one["native_abi_sha256"] != larger["native_abi_sha256"]
    # Exercise the selection transition using two real retained ABIs under a
    # shared population key. ABI identity must survive even when every other
    # selector dimension agrees; this is not a new capture acceptance claim.
    larger = {**larger, "source_identity": one["source_identity"], "geometry": one["geometry"]}
    newer = {**one, "receipt": {"path": "newer", "sha256": "newer"},
             "group_id": "fresh-program-group"}
    selected = module.select_references([one, larger, newer], {})
    assert selected == [newer, larger]


def test_v41_merged_native_partitions_keep_full_population_and_unscored_gaps(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    reviewer = importlib.import_module("review_priority_decode_scoreboard")
    source = root / "examples/structure/acceptance-20261030-v41-native-references-0b822d0e/v41-native-reference-scoreboard.json"
    original = json.loads(source.read_text())
    report = module.build([], [], [source])
    rows = report["current_source_role_references"]
    assert len(rows) == 63
    assert sum(row["observed_us"]["count"] for row in rows) == 83000
    assert sum(item["event_count"] for case in original["cases"] for item in case["unresolved"]) == 99600
    groups = {(case["case_id"], group["group_id"]): group
              for case in original["cases"] for group in case["groups"]}
    for row in rows:
        expected = groups[row["case_id"], row["group_id"]]
        assert row["partition_indices"] == expected["partition_indices"]
        assert row["observed_us"] == expected["observed_us"]
        assert not row["scored"] and not row["additional_budget_allowed"]
    assert report["summary"]["operator_accuracy_by_tier"] == {
        "heavy_relative_15pct": {"compared": 0, "passed": 0},
        "micro_absolute_15us": {"compared": 0, "passed": 0}}
    path = tmp_path / "v41-priority.json"
    path.write_text(json.dumps(report))
    check = reviewer.review(path)
    assert check["status"] == "passed", check["failures"]


def test_v41_composed_references_preserve_all_three_evidence_domains(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    reviewer = importlib.import_module("review_priority_decode_scoreboard")
    base = root / "examples/structure"
    v41 = base / "acceptance-20261030-v41-composed-native-5ec8843a/v41-complete-reference-scoreboard.json"
    glm = base / "acceptance-20261030-glm-source-complete-operators/glm-native-reference-scoreboard.json"
    original = json.loads(v41.read_text())
    originals = {(case["case_id"], group["group_id"]): group
                 for case in original["cases"] for group in case["groups"]}
    report = module.build([], [], [glm, v41])
    rows = [row for row in report["current_source_role_references"] if row["receipt"]["path"] == str(v41.resolve())]
    assert len(rows) == 98
    assert sum(row["observed_us"]["count"] for row in rows) == 398400
    assert report["summary"]["current_operator_scored_events"] == 0
    assert report["summary"]["operator_accuracy_by_tier"] == {
        "heavy_relative_15pct": {"compared": 0, "passed": 0},
        "micro_absolute_15us": {"compared": 0, "passed": 0}}
    domains = {}
    for row in rows:
        group = originals[row["case_id"], row["group_id"]]
        domain = row["observation_identity_domain"]
        domains[domain] = domains.get(domain, 0) + 1
        assert row["observed_us"] == group["observed_us"]
        assert row["source_correspondence"] == group["source_correspondence"]
        assert row["conditions"] == group.get("conditions")
        assert row["retained_group_id"] == group.get("retained_group_id")
        assert row["retained_cohort_id"] == group.get("retained_cohort_id")
        assert row["cohort_id"] == group.get("cohort_id")
        assert row["observed_contract"] == group.get("observed_contract")
        assert not row["scored"] and not row["additional_budget_allowed"]
        if "partition_indices" not in group and "partition_index" not in group:
            assert row["partition_indices"] is None
        if domain != "full_native_abi":
            assert row["native_abi_sha256"] is None
            assert "native_abi" not in row["evidence_strength"]
    assert domains == {"full_native_abi": 49, "source_symbol_retained_group": 21, "normalized_contract": 28}
    # Independent derivation of the existing complete-ABI key: the new tagged
    # identity must not change old GLM generation selection.
    legacy = json.loads(glm.read_text())
    old_keys = set()
    for case in legacy["cases"]:
        geo = case["geometry"]
        population = (case["source_identity"]["sha256"], geo["query_rows"], geo["tokens_per_sequence"], geo["sequences_per_replica"])
        for group in case["groups"]:
            abi_sha = hashlib.sha256(json.dumps(group["native_abi"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            old_keys.add((population, group["native_operator_type"], (group["declared_role"],), tuple(sorted(group["layer_ids"])), abi_sha))
    actual_keys = {(module._population(row), row["native_operator_type"], tuple(sorted(row["declared_roles"])),
                   tuple(sorted(row["layer_ids"])), row["native_abi_sha256"])
                  for row in report["current_source_role_references"] if row["receipt"]["path"] == str(glm.resolve())}
    assert len(old_keys) == 45 and actual_keys == old_keys
    output = tmp_path / "composed-references.json"
    output.write_text(json.dumps(report))
    # The reviewer must not consult the production observation selector.
    monkeypatch.setattr(module, "reference_observation_identity", lambda *_: pytest.fail("review imported producer"))
    check = reviewer.review(output)
    assert check["status"] == "passed", check["failures"]
    weakened = next(row for row in rows if row["observation_identity_domain"] == "source_symbol_retained_group")
    weakened["native_abi_sha256"] = hashlib.sha256(b"null").hexdigest()
    weakened["evidence_strength"] = "complete_native_abi_conditional_program_reference"
    output.write_text(json.dumps(report))
    check = reviewer.review(output)
    assert check["status"] == "failed"
    assert "All conditional references retain evidence and remain unscored" in check["failures"]


def test_latest_v41_reference_keeps_distinct_source_symbol_groups_without_null_abi_collision(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    source = root / "examples/structure/acceptance-20261030-v41-composed-native-5ec8843a/v41-complete-reference-scoreboard.json"
    case = json.loads(source.read_text())["cases"][0]
    old = module.native_reference_rows(case, {"path": "old", "sha256": "old"})
    newer = [{**row, "receipt": {"path": "new", "sha256": "new"}, "group_id": "new-cost-" + row["group_id"]} for row in old]
    assert module.select_references(old + newer, {}) == newer
    symbol = [row for row in old if row["observation_identity_domain"] == "source_symbol_retained_group"]
    assert len(symbol) == 3 and all(row["native_abi_sha256"] is None for row in symbol)
    # Hold the other selector fields equal to exercise evidence identity alone;
    # these remain copied real observations, not a new capture acceptance.
    shared_layer_set = [{**row, "layer_ids": symbol[0]["layer_ids"]} for row in symbol]
    assert len(module.select_references(shared_layer_set, {})) == 3
    assert len({row["observation_identity_sha256"] for row in symbol}) == 3
