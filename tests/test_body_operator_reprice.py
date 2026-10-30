"""Retained GLM router observations versus independently rebuilt Sim declarations."""
from copy import deepcopy
from dataclasses import replace
import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PREFIX = ROOT / "examples/structure/acceptance-20261030-glm-operators-09811dad/body-operator-a5_glm53flash_tp8_c32_p4k-glm-flash-ws9"


@pytest.fixture(scope="module")
def reprice():
    pytest.importorskip("mindie_sim.structure")
    import sys
    sys.path.insert(0, str(ROOT / "examples/structure"))
    return importlib.import_module("reprice_body_operator_families")


@pytest.fixture(scope="module")
def retained(reprice):
    mapping = reprice.read(PREFIX.with_suffix(".mapping.json"))
    roles = mapping["conditional_role_by_cohort_id"]
    mapping = {**mapping, "windows": [{**window, "cohorts": [row for row in window["cohorts"]
                if roles[row["cohort_id"]] == ["router"]]} for window in mapping["windows"]]}
    actual = reprice.read(PREFIX.with_suffix(".actual.json"))
    manifest = reprice.fresh_structure(PREFIX.with_suffix(".case.json"), mapping)
    rebound, _ = reprice.rebind_mapping(mapping, manifest, actual["source_identity"])
    assert len(rebound["windows"][0]["cohorts"]) == 1
    return actual, mapping, rebound, manifest


def test_real_router_rebind_keeps_exact_observations_and_uses_new_work(reprice, retained):
    actual, original, rebound, manifest = retained
    old, new = original["windows"][0]["cohorts"][0], rebound["windows"][0]["cohorts"][0]
    assert old["contract"] == ["matrix", [128, 288, 4096], "fp32", "fp32", "fp32", [], ""]
    assert new["event_count"] == 1302
    for field in ("complete_activity_sum_ns", "duration_ns", "busy_union_ns", "status_counts"):
        assert new[field] == old[field]
    same, plan = reprice.rebind_mapping(rebound, manifest, actual["source_identity"])
    assert same is rebound
    assert plan["mode"] == "identical_declaration_new_cost"


def test_real_failed_worker_receipt_is_visible_before_the_next_program(reprice, capsys):
    import json
    directory = ROOT / "examples/structure/acceptance-20261030-v41-composed-operators-ec58ce79/a5_v41_fp8_tp1_dp8_ep8_c32_p2k"
    report = reprice.read(next(directory.glob("*.comparison.json")))
    receipt = report["program_receipts"][0]
    reprice.print_program_progress("retained-c32-pilot", 1, len(report["program_receipts"]), receipt)
    progress = json.loads(capsys.readouterr().out)
    for key in ("reason", "returncode", "stderr", "elapsed_seconds", "timeout_seconds"):
        assert progress[key] == receipt[key]
    assert "comparison_worker_exceeds_512_mib" in progress["stderr"]
    assert progress["status"] == "failed" and progress["program"] == 1


def router_declaration(retained, changed_indices):
    from mindie_sim.prediction.operator_analysis import target_graphs
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_op_structure
    _, _, _, manifest = retained
    import json
    case = parse_case(json.loads(PREFIX.with_suffix(".case.json").read_text()))
    geometry = {key: manifest["execution"][key] for key in ("phase", "tokens", "context", "sequences", "scope")}
    graphs = target_graphs(case, **geometry)
    routers = tuple(op for op in graphs[0] if op.op_id.endswith(".router"))
    # A controlled implementation declaration changes memory work while the
    # real captured tensor contract remains identical. No duration is fitted.
    changed = tuple(replace(op, hbm_bytes=op.hbm_bytes * 2, mte2_bytes=op.mte2_bytes * 2)
                    if index in changed_indices else op for index, op in enumerate(routers))
    return export_op_structure(changed, model=manifest["model"], execution=manifest["execution"],
                               kernels=case.runtime.kernels)


def test_uniform_work_change_rebinds_without_reusing_old_physical_work(reprice, retained):
    actual, _, rebound, _ = retained
    manifest = router_declaration(retained, range(42))
    fresh, plan = reprice.rebind_mapping(rebound, manifest, actual["source_identity"])
    assert not plan["excluded"]
    before = rebound["windows"][0]["cohorts"][0]
    after = fresh["windows"][0]["cohorts"][0]
    assert after["physical_work_per_instance"]["hbm_bytes"] == 2 * before["physical_work_per_instance"]["hbm_bytes"]
    assert after["physical_signature"] != before["physical_signature"]
    assert after["duration_ns"] == before["duration_ns"]


def test_new_heterogeneous_candidate_group_does_not_split_old_histogram(reprice, retained):
    actual, _, rebound, _ = retained
    manifest = router_declaration(retained, {0})
    fresh, plan = reprice.rebind_mapping(rebound, manifest, actual["source_identity"])
    assert fresh["windows"][0]["cohorts"] == []
    assert plan["excluded"][0]["reason"] == "candidate_physical_work_differs"
    assert plan["excluded"][0]["event_count"] == 1302
    assert fresh["windows"][0]["cohort_excluded_event_counts"]["rebind:candidate_physical_work_differs"] == 1302


def test_changed_tensor_geometry_cannot_promote_two_examples(reprice, retained):
    actual, _, rebound, _ = retained
    changed = deepcopy(rebound)
    changed["declared_execution"] = {**changed["declared_execution"], "tokens": 1}
    manifest = reprice.fresh_structure(PREFIX.with_suffix(".case.json"), changed)
    fresh, plan = reprice.rebind_mapping(rebound, manifest, actual["source_identity"])
    assert fresh["windows"][0]["cohorts"] == []
    assert plan["excluded"][0]["reason"] == "observed_contract_or_semantic_candidate_set_changed"
    assert plan["excluded"][0]["event_count"] == 1302


def test_global_projection_does_not_duplicate_exact_histograms(reprice, retained):
    actual, _, _, _ = retained
    projected = reprice.compact_case(actual["families"])
    assert sum(f["observed_us"]["count"] for f in projected) == actual["counts"]["selected_body_events"]
    assert all("duration_ns_counter" not in f and "examples" not in f for f in projected)
    assert all("duration_ns_counter" not in group for f in projected for group in f["structure_groups"])


def test_other_real_capture_mapping_cannot_join_this_source(reprice, retained):
    actual, original, _, _ = retained
    reprice.validate_observation_join(actual, original)
    other = reprice.read(PREFIX.with_name(PREFIX.name.replace("c32_p4k", "c32_p8k")).with_suffix(".mapping.json"))
    with pytest.raises(ValueError, match="mapping_and_actual_source_identity_differ"):
        reprice.validate_observation_join(actual, other)


def test_partial_real_mqsmla_groups_preserve_full_family_population(reprice):
    prefix = ROOT / "examples/structure/acceptance-20261030-v41-operators-09811dad/body-operator-a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1-v41-dp8"
    actual = reprice.read(prefix.with_suffix(".actual.json"))
    mapping = reprice.read(prefix.with_suffix(".mapping.json"))
    groups = [group for group in actual["source_role_references"] if group["native_operator_type"] == "MqsmlaKernel___call__"]
    assert len(groups) > 1
    excluded = [{"native_operator_type": group["native_operator_type"], "declared_role": group["declared_role"],
                 "event_count": group["observed_us"]["count"], "reason": "source_program_changed"} for group in groups[1:]]
    rows = reprice.repriced_family_rows(actual, mapping, {"windows": []}, {"_source_role_groups": groups[:1]}, excluded)
    family = next(row for row in rows if row["native_operator_type"] == "MqsmlaKernel___call__")
    counts = family["source_reference_coverage"]
    assert counts["reference_event_count"] == groups[0]["observed_us"]["count"]
    assert counts["excluded_reference_event_count"] == sum(g["observed_us"]["count"] for g in groups[1:])
    assert counts["reference_event_count"] + counts["excluded_reference_event_count"] == family["observed_us"]["count"]
    assert family["scored_event_count"] == family["passed_cohort_count"] == 0
    assert family["duration_ns_counter"] == next(row for row in actual["families"] if row["native_operator_type"] == "MqsmlaKernel___call__")["duration_ns_counter"]


def test_reference_retry_preserves_successful_real_strict_comparison(reprice):
    row = {key: reprice.identity(PREFIX.with_suffix(suffix)) for key, suffix in (
        ("actual_identity", ".actual.json"), ("mapping_identity", ".mapping.json"),
        ("case_identity", ".case.json"), ("comparison_identity", ".comparison.json"))}
    runtime = reprice.runtime_identity()
    actual, mapping, comparison = reprice.validate_reference_retry(row, runtime, runtime)
    assert actual["forward_count"] == 31
    assert comparison["graph_id"] == mapping["graph_id"]
    assert comparison["status_counts"]["compared"] == 19
    assert all(receipt["status"] == "completed" for receipt in comparison["program_receipts"])


def test_reference_retry_rejects_new_sim_cost_under_old_success_receipt(reprice):
    row = {key: reprice.identity(PREFIX.with_suffix(suffix)) for key, suffix in (
        ("actual_identity", ".actual.json"), ("mapping_identity", ".mapping.json"),
        ("case_identity", ".case.json"), ("comparison_identity", ".comparison.json"))}
    runtime = reprice.runtime_identity()
    changed = dict(runtime)
    sim_file = next(path for path in reprice.sim_sources(changed) if path.endswith("cohort_comparison.py"))
    changed[sim_file] = "changed-cost-source"
    with pytest.raises(ValueError, match="reference_retry_sim_runtime_changed"):
        reprice.validate_reference_retry(row, runtime, changed)
