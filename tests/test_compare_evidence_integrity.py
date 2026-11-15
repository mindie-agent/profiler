"""Evidence-integrity checks for C7 comparison, reporting, and compare CLI.

These tests exercise the real ``analyze_profile`` producer, not synthetic
comparison dictionaries, so a declared C7 value is always checked against the
window rows that produced it.  No device or model initialization is used.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from mindie_profiler import Window, analyze_profile
from mindie_profiler.__main__ import main
from mindie_profiler.compare import compare_profiles
from tests.test_profiler_core import RANK0_ID, RANK1_ID, STEP4, STEP5, build_run

SCENE = {
    "framework": "vllm-ascend",
    "phase": "decode",
    "tp": 1,
    "dp": 1,
    "graph_mode": "eager",
    "clock_domain": "aligned_syscnt",
    "input_signature": "evidence-integrity-fixed-input",
    "runtime": {"soc": "Ascend910B4", "framework": {"torch_npu": "2.10.0.post4"}},
    "device": {"card": 0, "host": "a3-165"},
    "model": "test-mlp",
    "shape": [8, 1024],
    "dtype": "float32",
}


def _report(root, *, windows=(STEP4, STEP5), scene=SCENE, ranks=(RANK0_ID,)):
    return analyze_profile(
        root,
        ranks=list(ranks) if ranks is not None else None,
        windows=list(windows),
        scene=dict(scene) if scene is not None else None,
    )


def _limitation_codes(receipt):
    return [item.get("code") for item in receipt.get("limitations", [])]


def _reasons(receipt):
    return [item.get("code") for item in receipt.get("reasons", [])]


def test_declared_step_p50_must_match_its_own_window_rows(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    raw_rows = {row["step"]: row["observed_event_span_ms"] for row in baseline["window_accounting"]}
    assert raw_rows == {STEP4.step: 0.045, STEP5.step: 0.025}
    # The report rows are 0.045/0.025; a declared 0.099 is stale, not a new
    # observation.  It must not produce a plausible 0.064 ms delta.
    baseline["step_accounting"]["observed_event_span_ms_p50"] = 0.099
    baseline["step_accounting"]["wall_ms_p50"] = 0.099

    receipt = compare_profiles(baseline, candidate)

    metric = receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]
    assert metric["status"] == "not_comparable"
    assert metric["reason"] == "declared_p50_inconsistent_with_window_accounting"
    assert metric["delta"] is None
    assert metric["relative_delta_pct"] is None
    provenance = metric["p50_provenance"]["baseline"]
    assert provenance["comparison_basis"] == "declared_p50"
    assert provenance["declared_p50"] == 0.099
    assert provenance["declared_value"] == 0.099
    assert provenance["recomputed_from_window_accounting"] == 0.035
    assert provenance["aligned_observation_count"] == 2
    assert provenance["declared_used"] is True
    assert provenance["declared_consistent"] is False
    assert metric["p50_provenance"]["candidate"]["declared_consistent"] is True
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert "declared_p50_inconsistent_with_window_accounting" in _limitation_codes(receipt)
    # Other untouched metrics remain comparable; the inconsistent summary does
    # not erase the rest of the evidence.
    assert receipt["comparable"] is True
    assert receipt["status"] == "comparable_with_limitations"
    assert receipt["step_accounting"]["metrics"]["device_busy_union_ms_p50"]["status"] == "compared"


def test_declared_block_p50_and_share_must_match_rows(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    attention = next(
        row for row in baseline["semantic_block_breakdown"] if row["block"] == "Attention"
    )
    assert attention["share_denominator"] == "sum_of_attributed_block_unions"
    assert attention["share_denominator_ms_p50"] == 0.035
    attention["busy_union_ms_p50"] = 0.099
    attention["share_of_busy_pct"] = 99.0

    receipt = compare_profiles(baseline, candidate)

    block = next(row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")
    assert block["status"] == "not_comparable"
    assert block["reason"] == "declared_block_p50_inconsistent_with_window_accounting"
    assert block["delta_ms"] is None
    assert block["share_delta_pp"] is None
    assert block["p50_provenance"]["baseline"]["recomputed_from_window_accounting"] == 0.01
    assert block["share_p50_provenance"]["baseline"]["recomputed_from_window_accounting"] == 31.111111
    assert block["share_denominator"] == "sum_of_attributed_block_unions"
    assert block["baseline_share_denominator_ms_p50"] == 0.035
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert "declared_block_p50_inconsistent_with_window_accounting" in _limitation_codes(receipt)
    assert "declared_block_share_inconsistent_with_window_accounting" in _limitation_codes(receipt)
    assert receipt["semantic_blocks"]["status"] == "comparable_with_limitations"


def test_missing_common_row_and_out_of_boundary_rows_keep_the_present_side(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    candidate["window_accounting"] = [
        row for row in candidate["window_accounting"] if row["step"] != STEP5.step
    ]

    receipt = compare_profiles(baseline, candidate)

    # The legacy key list stays compact; the new evidence keeps the actual row.
    assert receipt["matching"]["steps"]["missing"] == [
        {"step": 5, "rank_id": RANK0_ID}
    ]
    unpaired = receipt["unpaired_observations"]
    assert len(unpaired) == 1
    assert unpaired[0]["present_in"] == ["baseline"]
    assert unpaired[0]["absent_from"] == ["candidate"]
    assert unpaired[0]["present_rows"]["baseline"]["observed_event_span_ms"] == 0.025
    assert receipt["applicability"]["unpaired_observation_count"] == 1

    step4_only = _report(root, windows=(STEP5,))
    excluded_receipt = compare_profiles(baseline, step4_only)
    assert excluded_receipt["matching"]["steps"]["basis"] == "recomputed_from_window_accounting"
    excluded = excluded_receipt["excluded_observations"]
    assert len(excluded) == 1
    assert excluded[0]["side"] == "baseline"
    assert excluded[0]["step"] == 4
    assert excluded[0]["reason"] == "step_outside_common_boundary"
    assert excluded[0]["row"]["observed_event_span_ms"] == 0.045
    assert excluded_receipt["applicability"]["excluded_observation_count"] == 1


def test_local_duration_survives_without_a_sourced_clock_mapping(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)

    receipt = compare_profiles(baseline, candidate)
    clock = receipt["matching"]["clock_domain"]

    # The scene labels match, but per-window coverage has no comparable event.
    # Local durations are still comparable; absolute timelines are not.
    assert clock["status"] == "match"
    assert clock["timeline_alignment_available"] is False
    assert clock["timeline_alignment_reason"] == "clock_coverage_incomplete"
    assert clock["source_clock_evidence"]["baseline"]["event_count"] == 13
    assert clock["source_clock_evidence"]["baseline"]["comparable_event_count"] == 0
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["status"] == "compared"

    def _map_clock(report, reference):
        for row in report["window_accounting"]:
            row["clock_coverage"] = {
                "status": "available",
                "event_count": 9,
                "comparable_event_count": 9,
                "mapped_event_count": 9,
                "mapped_endpoint_count": 20,
                "total_endpoint_count": 20,
                "mapped_window_endpoint_count": 2,
                "domains": ["db_task_ns"],
                "reference_domains": [reference],
                "reference_domain": reference,
            }

    _map_clock(baseline, "syscnt_ref")
    _map_clock(candidate, "syscnt_ref")
    mapped = compare_profiles(baseline, candidate)
    assert mapped["matching"]["clock_domain"]["timeline_alignment_available"] is True
    assert mapped["matching"]["clock_domain"]["timeline_alignment_basis"] == (
        "all_aligned_window_rows_shared_reference_domain:syscnt_ref"
    )
    assert mapped["step_accounting"]["metrics"]["wall_ms_p50"]["status"] == "compared"

    # Both ranks are present, but only rank 0 has mapped coverage.  A single
    # rank's reference name cannot make the whole comparison aligned.
    multi_baseline = _report(root, ranks=None)
    multi_candidate = _report(root, ranks=None)
    for row in multi_baseline["window_accounting"]:
        if row["rank_id"] == RANK0_ID:
            row["clock_coverage"] = {
                "status": "available", "event_count": 9, "comparable_event_count": 9,
                "mapped_event_count": 9, "mapped_endpoint_count": 20,
                "total_endpoint_count": 20, "mapped_window_endpoint_count": 2,
                "domains": ["db_task_ns"], "reference_domains": ["syscnt_ref"],
                "reference_domain": "syscnt_ref",
            }
    for row in multi_candidate["window_accounting"]:
        if row["rank_id"] == RANK0_ID:
            row["clock_coverage"] = {
                "status": "available", "event_count": 9, "comparable_event_count": 9,
                "mapped_event_count": 9, "mapped_endpoint_count": 20,
                "total_endpoint_count": 20, "mapped_window_endpoint_count": 2,
                "domains": ["db_task_ns"], "reference_domains": ["syscnt_ref"],
                "reference_domain": "syscnt_ref",
            }
    partial = compare_profiles(multi_baseline, multi_candidate)
    assert partial["matching"]["clock_domain"]["timeline_alignment_available"] is False
    assert partial["matching"]["clock_domain"]["timeline_alignment_reason"] == (
        "clock_coverage_incomplete"
    )
    assert partial["step_accounting"]["metrics"]["wall_ms_p50"]["status"] == "compared"

    # Two sides with different (each complete) references cannot be aligned.
    other = _report(root)
    _map_clock(other, "other_ref")
    conflict = compare_profiles(baseline, other)
    assert conflict["matching"]["clock_domain"]["timeline_alignment_available"] is False
    assert conflict["matching"]["clock_domain"]["timeline_alignment_reason"] == (
        "clock_reference_domain_mismatch"
    )
    assert conflict["step_accounting"]["metrics"]["wall_ms_p50"]["status"] == "compared"


def test_compare_cli_records_raw_input_hashes_and_keeps_empty_module_table_visible(
    tmp_path, capsys,
):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    for report in (baseline, candidate):
        report["structure"] = {"event_sequence_shape": [], "modules": [], "layers": []}
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    output = tmp_path / "comparison.json"

    code = main([
        "compare",
        "--baseline-summary", str(baseline_path),
        "--candidate-summary", str(candidate_path),
        "--output", str(output),
    ])
    capsys.readouterr()

    assert code == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    baseline_hash = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    candidate_hash = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    assert receipt["input_evidence"]["baseline"]["summary"]["sha256"] == baseline_hash
    assert receipt["input_evidence"]["candidate"]["summary"]["sha256"] == candidate_hash
    assert receipt["input_evidence"]["baseline"]["kind"] == "summary"
    assert receipt["input_evidence"]["baseline"]["scene"]["input_signature"] == SCENE["input_signature"]
    assert receipt["input_evidence"]["baseline"]["source_identity"]["sources"]
    assert receipt["generated_at_utc"]

    # Empty structure files stay visible as an incomplete module table instead
    # of being dropped from the receipt.
    assert receipt["tables"]["modules"]["status"] == "not_comparable"
    assert receipt["tables"]["modules"]["modules"] == []
    assert "module_table_not_comparable" in _limitation_codes(receipt)
    assert receipt["status"] == "comparable_with_limitations"

    # The output is still the same comparison the Python API produces.
    api_receipt = compare_profiles(
        baseline, candidate, require_binding=True, require_input_identity=True,
    )
    assert receipt["step_accounting"]["metrics"]["wall_ms_p50"]["status"] == \
        api_receipt["step_accounting"]["metrics"]["wall_ms_p50"]["status"]


def test_all_inconsistent_step_metrics_keep_the_receipt_inspectable(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    for key in (
        "observed_event_span_ms_p50",
        "device_busy_union_ms_p50",
        "device_activity_sum_ms_p50",
        "exposed_comm_ms_p50",
        "device_uncovered_ms_p50",
        "total_cost_ms_p50",
        "wall_ms_p50",
        "busy_union_ms_p50",
        "kernel_sum_ms_p50",
        "host_gap_ms_p50",
        "underfeed_bubble_ratio",
        "aicpu_exposed_ratio",
    ):
        baseline["step_accounting"][key] = 0.099

    receipt = compare_profiles(baseline, candidate)

    assert receipt["comparable"] is False
    assert receipt["status"] == "not_comparable"
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert "no_comparable_step_metrics" in [item["code"] for item in receipt["reasons"]]
    assert receipt["step_accounting"]["status"] == "not_comparable"
    assert receipt["step_accounting"]["metrics"]["wall_ms_p50"]["reason"] == (
        "declared_p50_inconsistent_with_window_accounting"
    )
    assert receipt["step_accounting"]["metrics"]["wall_ms_p50"]["delta"] is None
    # Independent semantic-block evidence survives the failed step summary.
    assert receipt["semantic_blocks"]["status"] == "comparable"
    attention = next(
        row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention"
    )
    assert attention["status"] == "compared"
    assert attention["baseline_busy_union_ms_p50"] == 0.01
    assert len(receipt["tables"]["semantic_blocks"]) == 7
    assert receipt["hierarchy"] is not None


def test_compare_cli_exits_4_on_declared_p50_integrity_failure(tmp_path, capsys):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    baseline["step_accounting"]["observed_event_span_ms_p50"] = 0.099
    baseline["step_accounting"]["wall_ms_p50"] = 0.099
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    output = tmp_path / "comparison.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

    code = main([
        "compare",
        "--baseline-summary", str(baseline_path),
        "--candidate-summary", str(candidate_path),
        "--output", str(output),
    ])
    capsys.readouterr()

    assert code == 4
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["comparable"] is True
    assert receipt["status"] == "comparable_with_limitations"
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["status"] == (
        "not_comparable"
    )
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["delta"] is None


def test_share_only_inconsistency_does_not_leave_block_status_comparable(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    attention = next(
        row for row in baseline["semantic_block_breakdown"] if row["block"] == "Attention"
    )
    attention["share_of_busy_pct"] = 99.0

    receipt = compare_profiles(baseline, candidate)

    block = next(row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")
    assert block["status"] == "compared"
    assert block["share_integrity"] == "failed"
    assert block["share_delta_pp"] is None
    assert receipt["semantic_blocks"]["status"] == "comparable_with_limitations"
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert "declared_block_share_inconsistent_with_window_accounting" in _limitation_codes(receipt)


def test_invalid_share_denominator_clears_share_deltas_and_cli_exits_4(tmp_path, capsys):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    attention = next(
        row for row in baseline["semantic_block_breakdown"] if row["block"] == "Attention"
    )
    attention["share_denominator_ms_p50"] = 0.099

    receipt = compare_profiles(baseline, candidate)
    block = next(row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")

    assert block["status"] == "compared"  # busy-union duration is independent
    assert block["delta_ms"] == 0.0
    assert block["share_delta_pp"] is None
    assert block["share_integrity"] == "failed"
    assert block["baseline_share_denominator_ms_p50"] == 0.035
    assert block["share_denominator_provenance"]["baseline"]["declared_consistent"] is False
    assert block["share_denominator_provenance"]["baseline"]["declared_value"] == 0.099
    assert block["share_denominator_provenance"]["baseline"]["declared_value"] == 0.099
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert "declared_block_share_denominator_inconsistent_with_window_accounting" in _limitation_codes(receipt)
    assert receipt["semantic_blocks"]["status"] == "comparable_with_limitations"
    table_block = next(
        row for row in receipt["tables"]["semantic_blocks"] if row["block"] == "Attention"
    )
    assert table_block["share_delta_pp"] is None
    assert receipt["step_accounting"]["metrics"]["device_busy_union_ms_p50"]["status"] == "compared"

    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    output = tmp_path / "comparison.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    code = main([
        "compare",
        "--baseline-summary", str(baseline_path),
        "--candidate-summary", str(candidate_path),
        "--output", str(output),
    ])
    capsys.readouterr()
    assert code == 4
    cli_receipt = json.loads(output.read_text(encoding="utf-8"))
    cli_block = next(row for row in cli_receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")
    assert cli_block["share_delta_pp"] is None


def test_invalid_ratio_p50_clears_delta_pp_and_bubble_table(tmp_path, capsys):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    baseline["step_accounting"]["underfeed_bubble_ratio"] = 0.099

    receipt = compare_profiles(baseline, candidate)
    metric = receipt["step_accounting"]["metrics"]["underfeed_bubble_ratio"]

    assert metric["status"] == "not_comparable"
    assert metric["reason"] == "declared_p50_inconsistent_with_window_accounting"
    assert metric["delta"] is None
    assert metric["delta_pp"] is None
    assert metric["relative_delta_pct"] is None
    assert metric["p50_provenance"]["baseline"]["declared_value"] == 0.099
    bubble = next(row for row in receipt["tables"]["bubble"] if row["name"] == "underfeed_bubble_ratio")
    assert bubble["delta"] is None
    assert bubble["delta_pp"] is None
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["status"] == "compared"

    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    output = tmp_path / "comparison.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    code = main([
        "compare",
        "--baseline-summary", str(baseline_path),
        "--candidate-summary", str(candidate_path),
        "--output", str(output),
    ])
    capsys.readouterr()
    assert code == 4
    cli_receipt = json.loads(output.read_text(encoding="utf-8"))
    assert cli_receipt["step_accounting"]["metrics"]["underfeed_bubble_ratio"]["delta_pp"] is None


def test_non_numeric_declared_p50_is_retained_without_crashing(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    baseline["step_accounting"]["observed_event_span_ms_p50"] = "N/A"

    receipt = compare_profiles(baseline, candidate)
    metric = receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]

    assert metric["status"] == "not_comparable"
    assert metric["reason"] == "declared_p50_not_numeric"
    assert metric["delta"] is None
    assert metric["p50_provenance"]["baseline"]["declared_value"] == "N/A"
    assert metric["p50_provenance"]["baseline"]["declared_invalid"] is True
    assert "declared_p50_not_numeric" in _limitation_codes(receipt)


def test_disjoint_steps_keep_both_side_observations_and_local_blocks(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root, windows=(STEP4,))
    candidate = _report(root, windows=(STEP5,))

    receipt = compare_profiles(baseline, candidate)

    assert receipt["status"] == "not_comparable"
    assert "steady_step_windows_disjoint" in _reasons(receipt)
    assert receipt["matching"]["steps"]["status"] == "disjoint"
    excluded = receipt["excluded_observations"]
    assert {(row["side"], row["step"], row["reason"]) for row in excluded} == {
        ("baseline", 4, "step_outside_common_boundary"),
        ("candidate", 5, "step_outside_common_boundary"),
    }
    assert all(row["source"] for row in excluded)
    assert receipt["local_step_accounting"]["baseline"]["observed_event_span_ms_p50"] == 0.045
    assert receipt["local_step_accounting"]["candidate"]["observed_event_span_ms_p50"] == 0.025
    assert {row["block"] for row in receipt["local_semantic_blocks"]["baseline"]} == {
        "Attention", "MoE", "Comm", "Norm", "Copy_Layout", "Unclassified", "Host_Gap",
    }
    assert {row["block"] for row in receipt["local_semantic_blocks"]["candidate"]} == {
        "Attention", "MoE", "Comm", "Norm", "Copy_Layout", "Unclassified", "Host_Gap",
    }


def test_disjoint_ranks_keep_both_side_observations_and_local_blocks(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root, windows=(STEP4,), ranks=(RANK0_ID,))
    candidate = _report(root, windows=(STEP4,), ranks=(RANK1_ID,))

    receipt = compare_profiles(baseline, candidate)

    assert receipt["status"] == "not_comparable"
    assert "rank_scope_disjoint" in _reasons(receipt)
    excluded = receipt["excluded_observations"]
    assert {(row["side"], row["rank_id"], row["reason"]) for row in excluded} == {
        ("baseline", RANK0_ID, "rank_outside_common_scope"),
        ("candidate", RANK1_ID, "rank_outside_common_scope"),
    }
    assert all(row["source"] for row in excluded)
    assert receipt["local_step_accounting"]["baseline"]["observed_event_span_ms_p50"] == 0.045
    assert receipt["local_semantic_blocks"]["candidate"]


def test_non_numeric_share_and_denominator_are_retained_without_crashing(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    attention = next(
        row for row in baseline["semantic_block_breakdown"] if row["block"] == "Attention"
    )
    attention["share_denominator_ms_p50"] = {"not": "numeric"}
    attention["share_of_busy_pct"] = "N/A"

    receipt = compare_profiles(baseline, _report(root))
    block = next(row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")

    assert block["status"] == "compared"  # busy-union duration still has raw rows
    assert block["share_delta_pp"] is None
    assert block["share_integrity"] == "failed"
    assert block["share_denominator_provenance"]["baseline"]["declared_value"] == {"not": "numeric"}
    assert block["share_p50_provenance"]["baseline"]["declared_value"] == "N/A"
    assert "declared_block_share_denominator_not_numeric" in _limitation_codes(receipt)
    assert "declared_block_share_not_numeric" in _limitation_codes(receipt)


def test_missing_share_denominator_declaration_recomputes_from_rows(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    attention = next(
        row for row in baseline["semantic_block_breakdown"] if row["block"] == "Attention"
    )
    attention.pop("share_denominator_ms_p50", None)

    receipt = compare_profiles(baseline, _report(root))
    block = next(row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")

    assert block["share_delta_pp"] == 0.0
    assert block["share_integrity"] == "consistent"
    assert block["share_denominator_status"]["baseline"] == "recomputed_missing_declaration"
    assert block["baseline_share_denominator_ms_p50"] == 0.035
    assert receipt["applicability"]["report_integrity"] == "consistent"


def test_missing_share_column_uses_complete_unions_and_rejects_declared_99(tmp_path, capsys):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    for row in baseline["window_accounting"]:
        mapping = row.get("block_share_pct")
        if isinstance(mapping, dict):
            mapping.pop("Attention", None)
    attention = next(
        row for row in baseline["semantic_block_breakdown"] if row["block"] == "Attention"
    )
    attention["share_of_busy_pct"] = 99.0

    receipt = compare_profiles(baseline, candidate)
    block = next(row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")

    assert block["share_delta_pp"] is None
    assert block["share_integrity"] == "failed"
    assert block["share_p50_provenance"]["baseline"]["declared_value"] == 99.0
    assert block["share_p50_provenance"]["baseline"]["recomputed_from_window_accounting"] == 31.111111
    assert block["baseline_share_of_busy_pct"] == 31.111111
    assert block["status"] == "compared"  # busy duration remains independent
    assert receipt["applicability"]["report_integrity"] == "failed"
    assert "declared_block_share_inconsistent_with_window_accounting" in _limitation_codes(receipt)

    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    output = tmp_path / "comparison.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    code = main([
        "compare",
        "--baseline-summary", str(baseline_path),
        "--candidate-summary", str(candidate_path),
        "--output", str(output),
    ])
    capsys.readouterr()
    assert code == 4


def test_missing_block_union_component_blocks_share_denominator(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    attention = next(
        row for row in baseline["semantic_block_breakdown"] if row["block"] == "Attention"
    )
    attention.pop("share_denominator_ms_p50", None)
    step4 = next(row for row in baseline["window_accounting"] if row["step"] == 4)
    step4["block_union_ms"].pop("MoE")

    receipt = compare_profiles(baseline, candidate)
    block = next(row for row in receipt["semantic_blocks"]["blocks"] if row["block"] == "Attention")

    assert block["share_delta_pp"] is None
    assert block["share_integrity"] == "not_verifiable"
    assert block["share_evidence"]["baseline"]["complete"] is False
    assert any(
        item.get("step") == 4 and "MoE" in (item.get("blocks") or [])
        for item in block["share_evidence"]["baseline"]["missing"]
    )
    assert block["baseline_share_denominator_ms_p50"] is None
    assert receipt["applicability"]["report_integrity"] == "incomplete"
    assert "share_evidence_incomplete" in _limitation_codes(receipt)
    assert "semantic_block_share_missing" not in _limitation_codes(receipt)


def test_input_identity_mismatch_keeps_both_sides_window_rows(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    baseline["scene"]["input_signature"] = "input-a"
    candidate["scene"]["input_signature"] = "input-b"

    receipt = compare_profiles(baseline, candidate, require_input_identity=True)

    assert receipt["status"] == "not_comparable"
    assert "input_identity_mismatch" in _reasons(receipt)
    rows = receipt["observation_rows"]
    assert len(rows) == 4
    assert {row["side"] for row in rows} == {"baseline", "candidate"}
    assert all(row["status"] == "excluded" for row in rows)
    assert all(row["reason"] == "input_identity_mismatch" for row in rows)
    assert sorted((row["step"], row["row"]["observed_event_span_ms"]) for row in rows) == [
        (4, 0.045), (4, 0.045), (5, 0.025), (5, 0.025),
    ]


def test_one_sided_window_accounting_keeps_available_rows(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    candidate["window_accounting"] = None

    receipt = compare_profiles(baseline, candidate)

    assert receipt["status"] == "not_comparable"
    assert "window_accounting_unavailable" in _reasons(receipt)
    rows = receipt["observation_rows"]
    assert len(rows) == 2
    assert {row["side"] for row in rows} == {"baseline"}
    assert all(row["status"] == "one_sided" for row in rows)
    assert all(row["reason"] == "peer_window_accounting_unavailable" for row in rows)
    assert sorted(row["row"]["observed_event_span_ms"] for row in rows) == [0.025, 0.045]


def test_report_projects_clock_source_facts_and_cross_rank_evidence(tmp_path):
    root = build_run(tmp_path)
    report = _report(root)
    source = report["source_identity"]["sources"][0]
    assert source["layout"] is None  # DB tables are not a CSV layout
    assert "COMPUTE_TASK_INFO" in source["table_kinds"]
    assert source["source_kind"] == "ascend_pytorch_profiler_db"
    assert source["clock"]["domain"] == "db_task_ns"
    assert source["clock_domains"][0]["reference_domain"] is None
    assert source["raw_ticks"]["retained_count"] == 13
    assert source["raw_ticks"]["samples"]
    assert source["raw_ticks"]["samples"][0]["step"] in (4, 5)
    assert source["read_errors"]["rows_read"] == 19
    assert source["source_ids"] and source["capture_ids"]
    assert report["source_identity"]["source_inventory"]["rank_count"] == 1
    assert report["source_identity"]["source_inventory"]["capture_count"] == 1
    assert report["source_identity"]["source_inventory"]["rank_sources"][0]["candidate_evidence"] == (
        "unavailable_from_analyze_source_ref"
    )
    cross = report["step_accounting"]["cross_rank"]
    assert "clock_union_span" in cross
    assert "straggler_and_link_attribution" in cross
    attribution = cross["straggler_and_link_attribution"]
    assert attribution["status"] in {"not_applicable", "applicable"}
    receipt = compare_profiles(report, _report(root))
    evidence = receipt["matching"]["clock_domain"]["cross_rank_evidence"]["baseline"]
    assert evidence["clock_union_span"] == cross["clock_union_span"]
    assert evidence["straggler_and_link_attribution"] == cross["straggler_and_link_attribution"]


def test_real_cann92_report_projects_layout_source_kind_clock_and_raw_ticks():
    fixture = Path(__file__).parent / "fixtures/profiler_core/cann92_mindstudio"
    report = analyze_profile(
        fixture,
        full_range=True,
        source="csv",
        scene={"framework": "vllm-ascend", "phase": "prefill", "clock_domain": "unknown"},
    )
    source = report["source_identity"]["sources"][0]
    assert source["layout"] == "op_summary"
    assert source["source_kind"] == "mindstudio_op_summary_csv"
    assert source["clock"]["domain"] == "mindstudio_op_summary_us"
    assert source["clock"]["reference_domain"] is None
    assert source["raw_ticks"]["retained_count"] == 15
    assert source["raw_ticks"]["samples"][0]["start_tick"] == "1794498607945358.570"
    assert source["raw_ticks"]["samples"][0]["duration_tick"] == "5.959"
    assert source["capture_ids"]
    assert report["source_identity"]["source_inventory"]["capture_count"] == 1


def test_compare_copies_full_clock_attribution_without_recomputing(tmp_path):
    root = build_run(tmp_path)
    baseline = _report(root)
    candidate = _report(root)
    cross = baseline["step_accounting"]["cross_rank"]
    cross["clock_union_span"] = {
        "status": "available",
        "reference_domain": "syscnt",
        "span_ms": 0.02,
    }
    cross["straggler_and_link_attribution"] = {
        "status": "applicable",
        "slow_link_evidence": [{"step": 4, "collective_index": 0, "rank_link_evidence": ["rank_0"]}],
        "slow_rank_evidence": [{"step": 4, "collective_index": 0, "perpetrator": "rank_0"}],
        "slow_link_rank_union": ["rank_0"],
    }
    receipt = compare_profiles(baseline, candidate)
    evidence = receipt["matching"]["clock_domain"]["cross_rank_evidence"]["baseline"]
    assert evidence["clock_union_span"] == cross["clock_union_span"]
    assert evidence["straggler_and_link_attribution"] == cross["straggler_and_link_attribution"]
    assert receipt["matching"]["clock_domain"]["source_clock_evidence"]["union_span"]["baseline"] == (
        cross["clock_union_span"]
    )


def _synthetic_clock_event(rank, start, end, *, domain="D0", reference="global_ns",
                           scale=2, offset=100, valid=(10, 100)):
    from mindie_profiler.events import ClockDomain, Event
    return Event(
        rank_id=rank, rank_index=int(rank.rsplit("_", 1)[1]),
        name="synthetic_kernel", op_type="MatMul", task_type="AI_CORE",
        core="AI_CORE", stream_id="1", task_id="1", device_id="0",
        start_ns=start, end_ns=end, source_kind="synthetic_capture", table="TASK",
        clock=ClockDomain(
            domain=domain, unit="tick", scale_ns=1, offset_ns=offset,
            reference_domain=reference, reference_scale_num=scale,
            reference_scale_den=1, valid_from_ns=valid[0], valid_to_ns=valid[1],
            source="explicit synthetic synchronization anchor",
        ),
        clock_start_tick=start, clock_end_tick=end,
    )


def _synthetic_clock_report(rows):
    from mindie_profiler.accounting import account_window
    from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
    from mindie_profiler.report import build_report
    observations = []
    sources = []
    for row in rows:
        rank, start, end, clock = row[:4]
        valid = row[4] if len(row) > 4 else (10, 100)
        window = Window(clock[0], clock[1], step=4, label="step_4")
        event = _synthetic_clock_event(rank, start, end, valid=valid)
        observations.append(Observation(
            rank_id=rank, rank_index=int(rank.rsplit("_", 1)[1]),
            window=window, accounting=account_window([event], window),
            events=[event], source=SourceRef(
                rank_id=rank, rank_index=int(rank.rsplit("_", 1)[1]),
                kind="synthetic_capture", path=f"{rank}.db", basename=f"{rank}.db",
                sha256=None, size_bytes=0, schema_version="test", schema_variant="test",
            ), stats=QueryStats(rank_id=rank, window_label="step_4"),
        ))
        sources.append(observations[-1].source)
    return build_report(
        sources=sources, observations=observations, requested_steps=[4],
        scene=dict(SCENE),
        scene_provided=True, limitations=[], query_timings=[], elapsed_ms=0,
        schema_rows=[], output_path=None, top_n=8,
    )


def test_clock_endpoint_validity_controls_c7_coverage_and_compare(tmp_path):
    # Event [101,111] is outside D0's [10,100] validity.  Window [100,120]
    # has only its start endpoint mappable, so the window is not a full proof.
    report = _synthetic_clock_report([
        ("rank_0", 101, 111, (100, 120)),
    ])
    coverage = report["window_accounting"][0]["clock_coverage"]
    assert coverage["event_count"] == 1
    assert coverage["mapped_event_count"] == 0
    assert coverage["mapped_window_endpoint_count"] == 1
    assert coverage["status"] == "unavailable_clock_relation"
    assert coverage["reason"] == "clock_coverage_incomplete"
    assert coverage["local_duration_ms"] == 0.000010
    assert coverage["mapped_duration_ms"] == 0.0

    receipt = compare_profiles(report, copy.deepcopy(report))
    clock = receipt["matching"]["clock_domain"]
    assert clock["timeline_alignment_available"] is False
    assert clock["timeline_alignment_reason"] == "clock_coverage_incomplete"
    assert clock["source_clock_evidence"]["baseline"]["mapped_event_count"] == 0
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["delta"] == 0.0
    assert receipt["matching"]["clock_domain"]["cross_rank_evidence"]["baseline"][
        "clock_union_span"
    ]["span_ns"] is None


def test_clock_window_scale_and_offset_map_to_120_140():
    report = _synthetic_clock_report([("rank_0", 10, 20, (10, 20), (10, 20))])
    coverage = report["window_accounting"][0]["clock_coverage"]
    assert coverage["window_start_mapped_ns"] == 120
    assert coverage["window_end_mapped_ns"] == 140
    assert coverage["mapped_event_count"] == 1
    assert coverage["local_duration_ms"] == 0.000010
    assert coverage["mapped_duration_ms"] == 0.000020
    assert coverage["status"] == "available"


def test_clock_partial_window_clips_before_mapping_and_keeps_local_duration():
    # Valid D0 [10,100]; event [90,110] clipped by [90,100] maps to [280,300].
    # Mapping the un-clipped event would be rejected at endpoint 110.
    report = _synthetic_clock_report([("rank_0", 90, 110, (90, 100))])
    coverage = report["window_accounting"][0]["clock_coverage"]
    assert coverage["event_count"] == 1
    assert coverage["mapped_event_count"] == 1
    assert coverage["mapped_endpoint_count"] == 4  # event endpoints + window endpoints
    assert coverage["window_start_mapped_ns"] == 280
    assert coverage["window_end_mapped_ns"] == 300
    assert coverage["local_duration_ms"] == 0.000010
    assert coverage["mapped_duration_ms"] == 0.000020
    assert coverage["status"] == "available"


def test_clock_two_ranks_one_out_of_validity_and_reference_conflict():
    # Rank 0 maps; rank 1's [90,100] endpoints are outside its [10,20]
    # validity.  The aggregate must stay incomplete, but rank 0's local
    # duration remains readable.
    out_of_range = _synthetic_clock_report([
        ("rank_0", 90, 100, (90, 100), (10, 100)),
        ("rank_1", 90, 100, (90, 100), (10, 20)),
    ])
    rank0 = out_of_range["window_accounting"][0]["clock_coverage"]
    rank1 = out_of_range["window_accounting"][1]["clock_coverage"]
    assert rank0["mapped_event_count"] == 1
    assert rank1["mapped_event_count"] == 0
    assert rank1["local_duration_ms"] == 0.000010
    candidate = copy.deepcopy(out_of_range)
    receipt = compare_profiles(out_of_range, candidate)
    assert receipt["matching"]["clock_domain"]["timeline_alignment_available"] is False
    assert receipt["matching"]["clock_domain"]["timeline_alignment_reason"] == (
        "clock_coverage_incomplete"
    )
    assert receipt["matching"]["clock_domain"]["cross_rank_evidence"]["baseline"][
        "clock_union_span"
    ]["span_ns"] is None


def _legacy_single_clock_coverage(report):
    """Replace the sourced coverage object with the r5 declaration shape.

    r5 declared ``comparable_event_count`` but no mapped event/endpoint/window
    fields.  The values are the exact old facts for the [101,111] event in a
    [100,120] window through D0->global_ns.
    """
    row = report["window_accounting"][0]
    row["clock_coverage"] = {
        "status": "available",
        "event_count": 1,
        "comparable_event_count": 1,
        "reference_domain": "global_ns",
        "domains": ["D0"],
    }
    for name in [key for key in row if str(key).startswith("comparison_")]:
        row.pop(name, None)
    return report


def test_legacy_single_clock_coverage_is_not_promoted_to_endpoint_proof():
    report = _synthetic_clock_report([("rank_0", 101, 111, (100, 120))])
    coverage = report["window_accounting"][0]["clock_coverage"]
    assert coverage["local_duration_ms"] == 0.000010
    _legacy_single_clock_coverage(report)

    receipt = compare_profiles(report, copy.deepcopy(report))
    clock = receipt["matching"]["clock_domain"]

    # The old declaration is retained as a declaration, not reinterpreted as
    # proof that the event or window endpoints were mapped.
    assert clock["timeline_alignment_available"] is False
    assert clock["timeline_alignment_reason"] == "clock_coverage_evidence_absent"
    evidence = clock["source_clock_evidence"]["baseline"]
    assert evidence["event_count"] == 1
    assert evidence["comparable_event_count"] == 1
    assert evidence["mapped_event_count"] is None
    assert evidence["mapped_endpoint_count"] is None
    assert evidence["mapped_window_endpoint_count"] is None
    assert evidence["unmapped_event_count"] is None
    assert any(
        gap.get("code") == "clock_coverage_evidence_absent"
        for gap in evidence["gaps"]
    )
    assert evidence["reference_domain"] is None
    # The local duration is still a valid observation and still compares.
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["delta"] == 0.0
    assert receipt["matching"]["clock_domain"]["cross_rank_evidence"]["baseline"][
        "clock_union_span"
    ]["span_ns"] is None


def test_legacy_row_list_clock_coverage_keeps_declared_counts_without_mapping():
    report = _synthetic_clock_report([("rank_0", 101, 111, (100, 120))])
    report["window_accounting"][0]["clock_coverage"] = {
        "status": "available",
        "rows": [{
            "event_count": 1,
            "comparable_event_count": 1,
            "reference_domain": "global_ns",
            "domains": ["D0"],
        }],
    }

    receipt = compare_profiles(report, copy.deepcopy(report))
    clock = receipt["matching"]["clock_domain"]
    evidence = clock["source_clock_evidence"]["baseline"]

    assert clock["timeline_alignment_available"] is False
    assert clock["timeline_alignment_reason"] == "clock_coverage_evidence_absent"
    assert evidence["event_count"] == 1
    assert evidence["comparable_event_count"] == 1
    assert evidence["mapped_event_count"] is None
    assert evidence["mapped_window_endpoint_count"] is None
    row = evidence["rows"][0]
    assert row["status"] == "clock_coverage_evidence_absent"
    assert any(
        gap.get("code") == "clock_coverage_evidence_absent"
        for gap in row["gaps"]
    )
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["delta"] == 0.0


def test_legacy_and_sourced_clock_coverage_mix_retains_the_valid_side():
    sourced = _synthetic_clock_report([("rank_0", 101, 111, (100, 120))])
    legacy = _legacy_single_clock_coverage(
        copy.deepcopy(_synthetic_clock_report([("rank_0", 101, 111, (100, 120))])))
    candidate_coverage = sourced["window_accounting"][0]["clock_coverage"]
    assert candidate_coverage["mapped_event_count"] == 0
    assert candidate_coverage["mapped_window_endpoint_count"] == 1

    receipt = compare_profiles(legacy, sourced)
    clock = receipt["matching"]["clock_domain"]
    evidence = clock["source_clock_evidence"]

    assert clock["timeline_alignment_available"] is False
    assert clock["timeline_alignment_reason"] == "clock_coverage_evidence_absent"
    assert evidence["baseline"]["event_count"] == 1
    assert evidence["baseline"]["comparable_event_count"] == 1
    assert evidence["baseline"]["mapped_event_count"] is None
    assert evidence["candidate"]["mapped_event_count"] == 0
    assert evidence["candidate"]["mapped_window_endpoint_count"] == 1
    assert evidence["candidate"]["reason"] == "clock_coverage_incomplete"
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["status"] == "compared"
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["delta"] == 0.0

    reversed_receipt = compare_profiles(sourced, legacy)
    reversed_clock = reversed_receipt["matching"]["clock_domain"]
    assert reversed_clock["timeline_alignment_available"] is False
    assert reversed_clock["timeline_alignment_reason"] == "clock_coverage_evidence_absent"
    assert reversed_clock["source_clock_evidence"]["baseline"]["mapped_event_count"] == 0
    assert reversed_clock["source_clock_evidence"]["candidate"]["mapped_event_count"] is None


def test_complete_clock_mapping_checks_declared_p50_in_the_projected_domain():
    report = _synthetic_clock_report([("rank_0", 10, 20, (10, 20), (10, 20))])
    row = report["window_accounting"][0]

    # The selected window keeps both facts: local [10,20] ns and the same
    # clipped endpoints through D0->global_ns at scale 2 -> [120,140] ns.
    assert row["observed_event_span_ms"] == 0.000010
    assert row["comparison_domain"] == "global_ns"
    assert row["comparison_complete"] is True
    assert row["comparison_observed_event_span_ms"] == 0.000020
    assert row["comparison_block_union_ms"]["Unclassified"] == 0.000020
    assert row["clock_coverage"]["window_start_mapped_ns"] == 120
    assert row["clock_coverage"]["window_end_mapped_ns"] == 140

    receipt = compare_profiles(report, copy.deepcopy(report))
    metric = receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]
    assert metric["status"] == "compared"
    assert metric["delta"] == 0.0
    assert metric["p50_provenance"]["baseline"]["recomputed_from_window_accounting"] == 0.000020
    assert receipt["matching"]["clock_domain"]["timeline_alignment_available"] is True

    block = next(
        item for item in receipt["semantic_blocks"]["blocks"]
        if item["block"] == "Unclassified"
    )
    assert block["status"] == "compared"
    assert block["p50_provenance"]["baseline"]["recomputed_from_window_accounting"] == 0.000020


def test_compare_cli_keeps_legacy_clock_gap_and_local_duration(tmp_path, capsys):
    baseline = _legacy_single_clock_coverage(
        _synthetic_clock_report([("rank_0", 101, 111, (100, 120))]))
    candidate = _legacy_single_clock_coverage(
        _synthetic_clock_report([("rank_0", 101, 111, (100, 120))]))
    baseline_path = tmp_path / "legacy-baseline.json"
    candidate_path = tmp_path / "legacy-candidate.json"
    output = tmp_path / "legacy-comparison.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

    code = main([
        "compare",
        "--baseline-summary", str(baseline_path),
        "--candidate-summary", str(candidate_path),
        "--output", str(output),
    ])
    capsys.readouterr()

    assert code == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    clock = receipt["matching"]["clock_domain"]
    assert clock["timeline_alignment_available"] is False
    assert clock["timeline_alignment_reason"] == "clock_coverage_evidence_absent"
    evidence = clock["source_clock_evidence"]["baseline"]
    assert evidence["event_count"] == 1
    assert evidence["comparable_event_count"] == 1
    assert evidence["mapped_event_count"] is None
    assert receipt["step_accounting"]["metrics"]["observed_event_span_ms_p50"]["delta"] == 0.0
