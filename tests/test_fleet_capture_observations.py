"""Tests for typed, independent fleet capture observations.

[Role]
  Lock the v2 observation contract: exact raw native-kernel mass is never
  divided by a declared/defaulted forward count; header-only exports are
  missing evidence; missing cores stay UNKNOWN; no neighbor rank/cell is
  borrowed; client metric semantics are explicit; no stale row value scores.

[Invariants]
  * Synthetic artifacts only; no `/Volumes/data` or simulator dependency.
  * Malformed cells raise; raw mass is invariant under `forward_steps` changes.
  * Each measurement boundary is separate and typed.

[Side-Effect Policy]
  Read-only over tmp_path; caches cleared per test.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pytest

_STRUCT_DIR = Path(__file__).resolve().parents[1] / "examples" / "structure"
if str(_STRUCT_DIR) not in sys.path:
    sys.path.insert(0, str(_STRUCT_DIR))

import fleet_capture_observations as obs  # noqa: E402
import fleet_capture_artifacts as artifacts  # noqa: E402
import fleet_capture_calls as calls  # noqa: E402
import fleet_source_discovery as discovery  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    results = tmp_path / "results"
    results.mkdir(exist_ok=True)
    receipts = tmp_path / "receipts.tsv"
    receipts.write_text("source_path\tsource_receipt_status\tusable_window_count\treceipt\n", encoding="utf-8")
    obs.configure_observation_roots(results_dir=results, receipt_index=receipts)
    obs.clear_caches()
    yield
    obs.clear_caches()


_KERNEL_HEADER = "Device_id,Task ID,Name,Type,Accelerator Core,Start Time(us),Duration(us)\n"


def _kernel_csv(path: Path, rows: list[tuple[str, str, float, float]]) -> Path:
    body = "".join(
        f"0,{idx},{name},{name},{core},{start:.3f},{dur:.3f}\n"
        for idx, (name, core, start, dur) in enumerate(rows)
    )
    path.write_text(_KERNEL_HEADER + body, encoding="utf-8")
    return path


def _row(**overrides) -> dict:
    row = {
        "capture_id": "extended_a3_a5_workstream_captures:run/cell",
        "suite": "extended_a3_a5_workstream_captures",
        "hardware_tier": "A5",
        "phase": "decode",
        "forward_steps": 32,
        "observed_ms": 10.0,
        "kernel_summary": {
            "total_kernel_rows": 4,
            "total_kernel_duration_us": 40000.0,
            "by_accelerator_core": {"AI_CORE": 20000.0, "MIX_AIV": 20000.0},
            "top_op_types": [{"type": "MoeDistributeCombineV2", "core": "MIX_AIV", "count": 2, "total_us": 20000.0}],
        },
    }
    row.update(overrides)
    return row


def _roots(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    obs.configure_observation_roots(data_roots=(root,), multinode_root=root)


def test_parse_kernel_details_exact_and_missing_core_is_unknown(tmp_path: Path) -> None:
    path = _kernel_csv(tmp_path / "kernel_details.csv", [
        ("MoeDistributeCombineV2", "MIX_AIV", 100.0, 30.0),
        ("MatMulV2", "AI_CORE", 110.0, 12.5),
        ("MoeDistributeCombineV2", "MIX_AIV", 130.0, 5.0),
        ("SomeOp", "", 140.0, 1.0),
    ])
    summary = obs.parse_kernel_details_summary(path)
    assert summary["total_kernel_rows"] == 4
    assert summary["total_kernel_duration_us"] == pytest.approx(48.5)
    assert summary["by_accelerator_core"] == {"AI_CORE": 12.5, "MIX_AIV": 35.0, "UNKNOWN": 1.0}
    assert summary["ops"]["SomeOp"]["core"] == "UNKNOWN"
    assert summary["first_start_us"] == pytest.approx(100.0)
    assert summary["last_end_us"] == pytest.approx(141.0)

    gz = tmp_path / "kernel_details.csv.gz"
    with gzip.open(gz, "wt", encoding="utf-8") as handle:
        handle.write(_KERNEL_HEADER)
        handle.write("0,0,X,X,AI_CORE,1.0,2.5\n")
    assert obs.parse_kernel_details_summary(gz)["total_kernel_duration_us"] == pytest.approx(2.5)


def test_malformed_cells_raise(tmp_path: Path) -> None:
    bad = tmp_path / "kernel_details.csv"
    bad.write_text(_KERNEL_HEADER + "0,0,X,X,AI_CORE,1.0,not-a-number\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed duration"):
        obs.parse_kernel_details_summary(bad)
    with pytest.raises(FileNotFoundError):
        obs.parse_kernel_details_summary(tmp_path / "absent.csv")

    good = tmp_path / "op_statistic.csv"
    good.write_text("OP Type,Core Type,Count,Total Time(us)\nMatMul,AI_CORE,3,60.0\n", encoding="utf-8")
    assert obs.parse_op_statistic_summary(good)["total_kernel_rows"] == 3
    for bad_count in ("2.5", "2.0", "NaN", "-1"):
        bad_dir = tmp_path / f"bad_{bad_count.replace('.', '_')}"
        bad_dir.mkdir()
        (bad_dir / "op_statistic.csv").write_text(
            f"OP Type,Core Type,Count,Total Time(us)\nMatMul,AI_CORE,{bad_count},60.0\n", encoding="utf-8")
        with pytest.raises(ValueError):
            obs.parse_op_statistic_summary(bad_dir)


def test_op_engine_cross_tab_preserves_heterogeneous_engines(tmp_path: Path) -> None:
    path = tmp_path / "op_statistic.csv"
    path.write_text(
        "OP Type,Core Type,Count,Total Time(us)\n"
        "MatMulV3,AI_CORE,10,1000.0\n"
        "MatMulV3,MIX_AIC,4,500.0\n"
        "FusedInferAttentionScore,MIX_AIC,2,300.0\n", encoding="utf-8")
    summary = artifacts.parse_op_statistic_summary(path)
    assert summary["ops"]["MatMulV3"]["core"] == "MIXED"
    assert summary["by_op_engine"]["MatMulV3\x1fAI_CORE"]["total_us"] == pytest.approx(1000.0)
    assert summary["by_op_engine"]["MatMulV3\x1fMIX_AIC"]["total_us"] == pytest.approx(500.0)
    scopes = obs.family_durations_us(summary)
    assert scopes["gemm"]["duration_us"] == pytest.approx(1500.0)
    assert scopes["gemm"]["by_core_us"] == {"AI_CORE": pytest.approx(1000.0), "MIX_AIC": pytest.approx(500.0)}
    assert scopes["gemm"]["op_types"]["MatMulV3"]["by_engine_us"] == {
        "AI_CORE": pytest.approx(1000.0), "MIX_AIC": pytest.approx(500.0)}


def test_scope_attribution_is_exact_not_allocated() -> None:
    summary = {"ops": {
        "MoeDistributeCombineV2": {"core": "MIX_AIV", "count": 2, "total_us": 30.0},
        "DispatchFFNCombine": {"core": "MIX_AIC", "count": 1, "total_us": 7.0},
        "MoeDistributeDispatchV3": {"core": "MIX_AIV", "count": 1, "total_us": 10.0},
        "MatMulV2": {"core": "AI_CORE", "count": 4, "total_us": 40.0},
        "hcom_allReduce_": {"core": "COMMUNICATION", "count": 1, "total_us": 20.0},
        "reduce_scatterAicpuKernel": {"core": "AI_CPU", "count": 1, "total_us": 3.0},
        "UnknownThing": {"core": "UNKNOWN", "count": 1, "total_us": 5.0},
    }}
    scopes = obs.family_durations_us(summary)
    assert scopes["moe.combine"]["duration_us"] == pytest.approx(37.0)
    assert set(scopes["moe.combine"]["op_types"]) == {"MoeDistributeCombineV2", "DispatchFFNCombine"}
    assert scopes["moe.dispatch"]["duration_us"] == pytest.approx(10.0)
    assert scopes["gemm"]["duration_us"] == pytest.approx(40.0)
    assert scopes["collective"]["duration_us"] == pytest.approx(23.0)
    assert scopes["other"]["duration_us"] == pytest.approx(5.0)
    assert sum(v["duration_us"] for v in scopes.values()) == pytest.approx(115.0)


def test_forward_steps_invariance_and_no_division(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = tmp_path / "run" / "cell"
    run.mkdir(parents=True)
    _kernel_csv(run / "kernel_details.csv", [("FusedInferAttentionScore", "MIX_AIC", 0.0, 140353.362)])
    _roots(monkeypatch, tmp_path)
    base = _row(capture_id="extended_a3_a5_workstream_captures:run/cell")
    a = obs.extract_capture_observations({**base, "forward_steps": 32})
    b = obs.extract_capture_observations({**base, "forward_steps": 2})
    for out in (a, b):
        assert out["evidence_status"] == "measured"
        assert out["native_kernel_mass_us"] == pytest.approx(140353.362)
        assert out["observed_operator_ms"] is None
        assert out["observed_by_core_ms"] == {}
        assert out["capture"]["declared_forward_steps_used_for_measurement"] is False
    assert a["measurements"]["whole_capture_native_kernel_rows"] == b["measurements"]["whole_capture_native_kernel_rows"]
    assert a["step_targets"] == b["step_targets"]


def test_header_only_is_missing_not_measured_and_row_never_scores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = tmp_path / "run" / "cell"
    run.mkdir(parents=True)
    (run / "export_summary.json").write_text(json.dumps({
        "total_kernel_rows": 0, "total_kernel_duration_us": 0,
        "by_accelerator_core": {}, "top_op_types": [], "worker_dir": "rank0", "rank_label": "active_rank"}), encoding="utf-8")
    (run / "kernel_details.csv.gz").write_bytes(gzip.compress(_KERNEL_HEADER.encode()))
    _roots(monkeypatch, tmp_path)
    row = _row(capture_id="extended_a3_a5_workstream_captures:run/cell", observed_ms=195.7604,
               kernel_summary={"total_kernel_rows": 11520, "total_kernel_duration_us": 6264332.81,
                               "by_accelerator_core": {"AI_CORE": 6264332.81}, "top_op_types": []})
    out = obs.extract_capture_observations(row)
    assert out["evidence_status"] == "missing_raw_kernel_rows"
    assert out["kernel_summary"] == {}
    assert out["native_kernel_mass_us"] is None
    assert out["measurements"]["whole_capture_native_kernel_rows"]["status"] == "zero_raw_kernel_rows"
    assert out["observed_operator_ms"] is None
    assert out["row_claimed"]["used_as_evidence"] is False
    assert out["row_claimed"]["matches_observed_times_declared_steps"] is True


def test_missing_active_rank_does_not_borrow_idle_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cell = tmp_path / "case" / "cell"
    idle = cell / "idle_dp_rank"
    idle.mkdir(parents=True)
    _kernel_csv(idle / "kernel_details.csv", [("MatMulV2", "AI_CORE", 0.0, 99.0)])
    _roots(monkeypatch, tmp_path)
    # exact capture is the cell root (no :idle_dp_rank); it has no artifact of its own
    row = _row(capture_id="a5_multinode_20261108:case:cell", suite="a5_multinode_full_coverage_20261108",
               kernel_summary={}, observed_ms=None)
    out = obs.extract_capture_observations(row)
    assert out["evidence_status"] == "missing_artifact"
    assert out["native_kernel_mass_us"] is None
    out_idle = obs.extract_capture_observations({**row, "capture_id": "a5_multinode_20261108:case:cell:idle_dp_rank"})
    assert out_idle["native_kernel_mass_us"] == pytest.approx(99.0)
    assert out_idle["identity"]["rank_selection"] == "idle_dp_rank"


def test_request_summary_ok_status_and_token_evidence(tmp_path: Path) -> None:
    path = tmp_path / "request_summary.csv"
    path.write_text(
        "tag,mode,req_idx,ok,status,ttft_ms,tpot_ms,e2e_ms,out_tokens,itl_p50_ms,itl_p90_ms,itl_p99_ms\n"
        "t,decode,0,1,200,100.0,20.0,1360.0,64,19.0,20.0,25.0\n"
        "t,decode,1,0,200,999.0,999.0,9999.0,64,999.0,999.0,999.0\n", encoding="utf-8")
    client = obs.parse_request_summary(path)
    assert client["requests"] == 2 and client["ok_requests"] == 1
    assert client["tpot_ms_median"] == pytest.approx(20.0)
    assert client["decode_token_count"] == 63
    assert client["decode_evidence"] == "client_decode_tokens"
    assert "producer out_tokens" in client["metric_semantics"]

    no_field = tmp_path / "no_field.csv"
    no_field.write_text("tag,mode,ok,status,ttft_ms,tpot_ms,e2e_ms\n"
                        "t,decode,1,200,100.0,20.0,1360.0\n", encoding="utf-8")
    assert obs.parse_request_summary(no_field)["decode_evidence"] == "unknown_completion_tokens"

    no_decode = tmp_path / "no_decode.csv"
    no_decode.write_text("tag,mode,ok,status,ttft_ms,out_tokens\n"
                         "t,prefill,1,200,883.6,1\n", encoding="utf-8")
    client = obs.parse_request_summary(no_decode)
    assert client["decode_token_count"] == 0 and client["decode_evidence"] == "no_decode_tokens"


def test_client_boundary_selected_without_arbitrary_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = tmp_path / "a5" / "run" / "cell"
    run.mkdir(parents=True)
    _kernel_csv(run / "kernel_details.csv", [("MatMulV2", "AI_CORE", 0.0, 1000.0)])
    (run / "request_summary.csv").write_text(
        "tag,mode,ok,status,ttft_ms,tpot_ms,e2e_ms,out_tokens\n"
        "t,decode,1,200,100.0,27.5,1825.0,64\n", encoding="utf-8")
    _roots(monkeypatch, tmp_path)
    out = obs.extract_capture_observations(_row(capture_id="extended_a3_a5_workstream_captures:a5/run/cell"))
    assert out["observed_ms"] == pytest.approx(27.5)
    assert out["observed_basis"] == "client_reported_tpot_producer_basis"
    assert out["measurements"]["native_client_request"]["status"] == "measured"
    # a decode row with TTFT only must not be promoted to TPOT
    (run / "request_summary.csv").write_text(
        "tag,mode,ok,status,ttft_ms,e2e_ms,out_tokens\n"
        "t,decode,1,200,100.0,1825.0,64\n", encoding="utf-8")
    obs.clear_caches()
    out2 = obs.extract_capture_observations(_row(capture_id="extended_a3_a5_workstream_captures:a5/run/cell"))
    assert out2["observed_ms"] is None
    assert out2["observed_basis"] is None


def test_timeline_max_end_and_bounded_streaming(tmp_path: Path) -> None:
    path = _kernel_csv(tmp_path / "kernel_details.csv", [
        ("_compute_slot_mapping_kernel", "AI_CORE", 0.0, 100.0),   # nested long interval
        ("MatMulV2", "AI_CORE", 10.0, 1.0),
        ("MatMulV2", "AI_CORE", 20.0, 1.0),
        ("MatMulV2", "AI_CORE", 260000.0, 1.0),
    ])
    tl = obs._kernel_timeline(path)
    assert tl["timeline_rows"] == 4
    assert tl["start_order"] == "nondecreasing"
    assert tl["wall_span_us"] == pytest.approx(260001.0)
    assert tl["busy_union_us"] == pytest.approx(100.0 + 1.0)  # gap splits at 100
    assert tl["max_gap_us"] == pytest.approx(259900.0)
    assert tl["step_marker_count"] == 1
    # out-of-order starts must not produce invented union/gap structure
    path2 = _kernel_csv(tmp_path / "kernel_details2.csv", [
        ("A", "AI_CORE", 10.0, 1.0), ("B", "AI_CORE", 0.0, 1.0)])
    tl2 = obs._kernel_timeline(path2)
    assert tl2["start_order"] == "out_of_order"
    assert tl2["busy_union_us"] is None and tl2["max_gap_us"] is None


def test_reported_scope_requires_same_capture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = tmp_path / "run" / "cell"
    run.mkdir(parents=True)
    raw = _kernel_csv(run / "kernel_details.csv", [("MatMulV2", "AI_CORE", 0.0, 1000.0)])
    sha = __import__("hashlib").sha256(raw.read_bytes()).hexdigest()
    results = tmp_path / "results"
    results.mkdir(exist_ok=True)
    receipts = tmp_path / "receipts.tsv"
    receipts.write_text("source_path\tsource_receipt_status\tusable_window_count\treceipt\n", encoding="utf-8")
    obs.configure_observation_roots(results_dir=results, receipt_index=receipts)
    # same capture: recorded path is the raw file itself
    (results / "decode.json").write_text(json.dumps({"cases": [{
        "case_id": "cell", "source": {"path": str(raw), "sha256": sha},
        "comparison": {"status": "compared", "observed_ms": 5.0,
                                       "metric_boundary": "target_body_device_graph"}}]}), encoding="utf-8")
    _roots(monkeypatch, tmp_path)
    row = _row(capture_id="registered_decode:cell")
    out = obs.extract_capture_observations(row)
    assert out["observed_ms"] is None  # no cross-boundary fallback
    assert obs.select_measurement(out, "producer_reported_device_forward_span") == pytest.approx(5.0)
    assert out["reported"]["same_artifact"] is True
    assert out["source"]["sha256"] == sha
    # different capture: must stay unknown, no borrowed report
    (results / "decode.json").write_text(json.dumps({"cases": [{
        "case_id": "other", "source": {"path": "/elsewhere/other/kernel_details.csv"},
        "comparison": {"status": "compared", "observed_ms": 9.0,
                                       "metric_boundary": "target_body_device_graph"}}]}), encoding="utf-8")
    obs.clear_caches()
    out2 = obs.extract_capture_observations(row)
    assert out2["observed_ms"] is None
    assert obs.select_measurement(out2, "producer_reported_device_forward_span") is None
    assert out2["measurements"]["producer_reported_device_forward_span"]["status"] == "unknown"


def test_unrelated_source_path_cannot_hijack_empty_rank(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cell = tmp_path / "case" / "cell"
    cell.mkdir(parents=True)
    other = tmp_path / "other" / "kernel_details.csv"
    other.parent.mkdir(parents=True)
    _kernel_csv(other, [("MatMulV2", "AI_CORE", 0.0, 456.0)])
    _roots(monkeypatch, tmp_path)
    row = _row(capture_id="a5_multinode_20261108:case:cell", suite="a5_multinode_full_coverage_20261108",
               kernel_summary={}, observed_ms=None, source_path=str(other))
    out = obs.extract_capture_observations(row)
    assert out["evidence_status"] == "missing_artifact"
    assert out["native_mass_us"] is None


def test_failed_row_cannot_prove_no_decode(tmp_path: Path) -> None:
    path = tmp_path / "request_summary.csv"
    path.write_text(
        "tag,mode,ok,status,ttft_ms,tpot_ms,e2e_ms,out_tokens\n"
        "t,decode,0,500,999.0,999.0,9999.0,1\n"       # failed row carries a count
        "t,decode,1,200,100.0,20.0,1360.0,\n", encoding="utf-8")  # successful but unknown count
    client = obs.parse_request_summary(path)
    assert client["ok_requests"] == 1 and client["failed_requests"] == 1
    assert client["successful_requests_missing_completion_tokens"] == 1
    assert client["decode_token_count"] is None
    assert client["decode_evidence"] == "unknown_completion_tokens"
    assert len(client["samples"]) == 2


def test_per_forward_window_uses_exact_kernel_match_only(tmp_path: Path) -> None:
    run = tmp_path / "run" / "cell"
    run.mkdir(parents=True)
    kernel = _kernel_csv(run / "kernel_details.csv", [("MatMulV2", "AI_CORE", 0.0, 1000.0)])
    windows = tmp_path / "windows.jsonl"
    windows.write_text(json.dumps({"kernel": str(kernel), "offset": 1, "portable_steps": 2,
                                   "portable_match": "exact",
                                   "steps": [{"gemm": 100.0, "attention": 50.0},
                                             {"gemm": 300.0, "attention": 50.0}]}) + "\n", encoding="utf-8")
    obs.configure_observation_roots(forward_windows=windows)
    _roots(None, tmp_path)  # keeps the configured window map
    obs.configure_observation_roots(data_roots=(tmp_path,), multinode_root=tmp_path, forward_windows=windows)
    out = obs.extract_capture_observations(_row(capture_id="extended_a3_a5_workstream_captures:run/cell"))
    fw = out["measurements"]["per_forward_window"]
    assert fw["status"] == "measured"
    assert fw["window_count"] == 2 and fw["offset"] == 1
    assert fw["family_total_us"] == {"attention": 100.0, "gemm": 400.0}
    assert fw["family_mean_us_per_window"] == {"attention": 50.0, "gemm": 200.0}
    assert obs.select_measurement(out, "per_forward_window") is None
    assert obs.select_measurement(out, "per_forward_window_additive") == pytest.approx(0.25)
    # a different kernel path must not borrow the window map
    other = tmp_path / "other" / "kernel_details.csv"
    other.parent.mkdir()
    _kernel_csv(other, [("MatMulV2", "AI_CORE", 0.0, 1000.0)])
    out2 = obs.extract_capture_observations(_row(capture_id="extended_a3_a5_workstream_captures:other"))
    assert out2["measurements"]["per_forward_window"]["status"] == "unknown"


def test_registered_extraction_provides_actual_forward_windows(tmp_path: Path) -> None:
    raw = tmp_path / "kernel_details.csv"
    raw.write_text("raw", encoding="utf-8")
    sha = __import__("hashlib").sha256(raw.read_bytes()).hexdigest()
    extraction = tmp_path / "extract.json"
    extraction.write_text(json.dumps({
        "status": "measured", "metric_boundary": "target_body_device_graph",
        "source_identity": {"path": str(raw), "size_bytes": raw.stat().st_size, "sha256": sha},
        "forwards": [
            {"body_forward_span_ms": 10.0, "body_activity_ms": 9.0,
             "geometry": {"query_rows": 6, "sequences_per_replica": 1, "tokens_per_sequence": 6}},
            {"body_forward_span_ms": 14.0, "body_activity_ms": 13.0,
             "geometry": {"query_rows": 6, "sequences_per_replica": 1, "tokens_per_sequence": 6}},
        ]}), encoding="utf-8")
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps({"cases": [{"case_id": "cell", "phase": "decode",
                                            "extraction_path": str(extraction)}]}), encoding="utf-8")
    obs.configure_observation_roots(cases_path=cases)
    out = obs.extract_capture_observations(_row(capture_id="registered_decode:cell"))
    fw = out["measurements"]["per_forward_window"]
    assert fw["status"] == "measured" and fw["window_count"] == 2
    assert fw["mean_forward_span_ms"] == pytest.approx(12.0)
    assert fw["geometry_populations"] == {"q=6,seq=1,tok=6": 2}
    assert obs.select_measurement(out, "per_forward_window") == pytest.approx(12.0)
    retagged = obs.extract_capture_observations({**_row(capture_id="registered_decode:cell"),
                                                 "forward_steps": 2, "geometry": {"layers": 999}})
    assert retagged["step_targets"]["per_forward_window_samples_ms"] == out["step_targets"]["per_forward_window_samples_ms"]


def test_registered_prefill_chunk_extraction_is_typed(tmp_path: Path) -> None:
    raw = tmp_path / "prefill_kernel_details.csv"
    raw.write_text("prefill", encoding="utf-8")
    sha = __import__("hashlib").sha256(raw.read_bytes()).hexdigest()
    extraction = tmp_path / "extract_prefill.json"
    extraction.write_text(json.dumps({
        "schema_version": "mindie-prefill-body-observation/1", "status": "measured",
        "source_identity": {"path": str(raw), "size_bytes": raw.stat().st_size, "sha256": sha},
        "forwards": [{"forward_id": "prefill:0", "phase": "prefill",
                      "body": {"span_ms": 542.751816, "device_activity_union_ms": 460.480058,
                               "start_ns": 1, "end_ns": 2}}]}), encoding="utf-8")
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps({"cases": [{"case_id": "cell", "phase": "prefill",
                                            "extraction_path": str(extraction)}]}), encoding="utf-8")
    obs.configure_observation_roots(cases_path=cases)
    out = obs.extract_capture_observations(_row(capture_id="registered_prefill:cell", phase="prefill"))
    fw = out["measurements"]["per_forward_window"]
    assert fw["status"] == "measured"
    assert fw["boundary"] == "per_forward_window_registered_prefill_chunk"
    assert fw["mean_forward_span_ms"] == pytest.approx(542.751816)
    assert obs.select_measurement(out, "per_forward_window") == pytest.approx(542.751816)


def test_source_receipt_index_matches_exact_kernel_path(tmp_path: Path) -> None:
    run = tmp_path / "run" / "cell"
    run.mkdir(parents=True)
    kernel = _kernel_csv(run / "kernel_details.csv", [("MatMulV2", "AI_CORE", 0.0, 1000.0)])
    sha = __import__("hashlib").sha256(kernel.read_bytes()).hexdigest()
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({
        "observed": {"status": "measured", "metric_boundary": "target_body_device_graph",
                     "source_identity": {"path": str(kernel), "size_bytes": kernel.stat().st_size, "sha256": sha},
                     "forwards": [{"body_forward_span_ms": 9.0, "body_activity_ms": 8.0,
                                   "geometry": {"query_rows": 4, "sequences_per_replica": 1,
                                                "tokens_per_sequence": 4}}]}}), encoding="utf-8")
    index = tmp_path / "receipts.tsv"
    index.write_text("source_path\tsource_receipt_status\tusable_window_count\tsize_match\tsource_sha256\treceipt\n"
                     f"{kernel}\tmeasured\t1\tTrue\t{sha}\t{receipt}\n", encoding="utf-8")
    obs.configure_observation_roots(data_roots=(tmp_path,), receipt_index=index)
    out = obs.extract_capture_observations(_row(capture_id="extended_a3_a5_workstream_captures:run/cell"))
    fw = out["measurements"]["per_forward_window"]
    assert fw["status"] == "measured" and fw["window_count"] == 1
    assert fw["mean_forward_span_ms"] == pytest.approx(9.0)
    # a different source file must not use the receipt
    other = tmp_path / "other" / "kernel_details.csv"
    other.parent.mkdir()
    _kernel_csv(other, [("MatMulV2", "AI_CORE", 0.0, 1000.0)])
    out2 = obs.extract_capture_observations(_row(capture_id="extended_a3_a5_workstream_captures:other"))
    assert out2["measurements"]["per_forward_window"]["status"] == "unknown"


def test_extraction_requires_actual_raw_digest_and_expected_sha(tmp_path: Path) -> None:
    raw = tmp_path / "kernel_details.csv"
    raw.write_text("raw-v1", encoding="utf-8")
    sha = __import__("hashlib").sha256(raw.read_bytes()).hexdigest()
    extraction = tmp_path / "extract.json"
    extraction.write_text(json.dumps({
        "status": "measured", "metric_boundary": "target_body_device_graph",
        "source_identity": {"path": str(raw), "size_bytes": raw.stat().st_size, "sha256": sha},
        "forwards": [{"body_forward_span_ms": 1.0}]}), encoding="utf-8")
    assert obs._extraction_scope(extraction, sha, "registered")["status"] == "measured"
    # changed expected SHA in a warm cache must not reuse a measured result
    assert obs._extraction_scope(extraction, "f" * 64, "registered")["status"] == "unknown"
    obs.clear_caches()
    # empty receipt source sha + expected sha must not be measured
    extraction.write_text(json.dumps({
        "status": "measured", "metric_boundary": "target_body_device_graph",
        "source_identity": {"path": str(raw), "size_bytes": raw.stat().st_size, "sha256": ""},
        "forwards": [{"body_forward_span_ms": 1.0}]}), encoding="utf-8")
    assert obs._extraction_scope(extraction, sha, "registered")["status"] == "unknown"
    obs.clear_caches()
    # raw bytes changed in place: receipt is stale, must not stay measured
    extraction.write_text(json.dumps({
        "status": "measured", "metric_boundary": "target_body_device_graph",
        "source_identity": {"path": str(raw), "size_bytes": raw.stat().st_size, "sha256": sha},
        "forwards": [{"body_forward_span_ms": 1.0}]}), encoding="utf-8")
    assert obs._extraction_scope(extraction, sha, "registered")["status"] == "measured"
    raw.write_text("raw-v2-longer", encoding="utf-8")
    obs.clear_caches()
    assert obs._extraction_scope(extraction, sha, "registered")["status"] == "unknown"


def test_unproven_reported_target_is_not_selected(tmp_path: Path) -> None:
    run = tmp_path / "run" / "cell"
    run.mkdir(parents=True)
    raw = _kernel_csv(run / "kernel_details.csv", [("MatMulV2", "AI_CORE", 0.0, 1000.0)])
    sha = __import__("hashlib").sha256(raw.read_bytes()).hexdigest()
    results = tmp_path / "results"
    results.mkdir(exist_ok=True)
    (results / "decode.json").write_text(json.dumps({"cases": [{
        "case_id": "cell", "source": {"path": str(raw), "sha256": sha},
        "comparison": {"status": "compared", "observed_ms": 5.0}}]}), encoding="utf-8")
    obs.configure_observation_roots(data_roots=(tmp_path,), results_dir=results)
    out = obs.extract_capture_observations(_row(capture_id="registered_decode:cell"))
    assert out["reported"]["status"] == "reported"
    assert out["reported"]["target_proven"] is False
    assert obs.select_measurement(out, "producer_reported_device_forward_span") is None
    assert out["step_targets"]["producer_reported_device_forward_span_ms"] is None


def test_native_calls_are_individual_positive_invocations(tmp_path: Path) -> None:
    path = tmp_path / "kernel_details.csv"
    path.write_text(
        "Device_id,Name,Type,Accelerator Core,Start Time(us),Duration(us),Input Shapes\n"
        "0,FusedInferAttentionScore,N/A,N/A,100.0,60.0,N/A\n"
        "0,FusedInferAttentionScore,N/A,N/A,170.0,61.0,N/A\n"
        "0,FusedInferAttentionScore,N/A,N/A,240.0,62.0,N/A\n", encoding="utf-8")
    scope = calls.parse_native_calls(path, capture_id="cal")
    assert scope["status"] == "measured" and scope["call_count"] == 3
    assert [c["span_us"] for c in scope["calls"]] == [60.0, 61.0, 62.0]
    assert all(c["engine"] == "UNKNOWN" and c["engine_known"] is False for c in scope["calls"])
    assert all(c["call_id"].startswith("cal:call") for c in scope["calls"])
    assert scope["source_sha256"]
    targets = calls.native_call_targets({"capture": {"capture_id": "cal"},
                                         "measurements": {"native_calls": {**scope, "capture_id": "cal"}}})
    assert [t["observed_ms"] for t in targets] == [0.06, 0.061, 0.062]
    assert all(t["capture_id"] == "cal" and t["engine_known"] is False for t in targets)
    assert all(t["source_fingerprint"]["sha256"] == scope["source_sha256"] for t in targets)
    import hf_sample_scoring as scorer
    table = scorer.observed_sample_table({"measurements": {"native_calls": scope}}, "native_calls")
    assert table["status"] == "measured" and len(table["keys"]) == 3
    assert table["values"] == [0.06, 0.061, 0.062]


def test_calibration_extract_exposes_per_call_targets(tmp_path: Path) -> None:
    cell = tmp_path / "calibration-20261107" / "a5" / "probe"
    cell.mkdir(parents=True)
    _kernel_csv_na(cell / "kernel_details.csv", [1.0, 2.0, 3.0])
    obs.configure_observation_roots(data_roots=(tmp_path,))
    out = obs.extract_capture_observations(_row(
        capture_id="operator_and_kernel_calibration_20261107:calibration-20261107/a5/probe",
        suite="operator_and_kernel_calibration_20261107"))
    assert out["measurements"]["native_calls"]["call_count"] == 3
    assert out["step_targets"]["native_call_samples_ms"] == [0.001, 0.002, 0.003]
    assert out["step_targets"]["native_call_engines"] == ["UNKNOWN"] * 3
    assert [t["engine_known"] for t in out["native_call_targets"]] == [False, False, False]


def _kernel_csv_na(path: Path, durations: list[float]) -> Path:
    lines = [f"0,FusedInferAttentionScore,N/A,N/A,{i * 10},{dur}\n"
             for i, dur in enumerate(durations)]
    path.write_text("Device_id,Name,Type,Accelerator Core,Start Time(us),Duration(us)\n" + "".join(lines),
                    encoding="utf-8")
    return path


def test_canonical_discovery_needs_no_task_tsv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "source" / "kernel_details.csv"
    raw.parent.mkdir(parents=True)
    raw.write_text("raw", encoding="utf-8")
    sha = __import__("hashlib").sha256(raw.read_bytes()).hexdigest()
    ext = tmp_path / "extractions"
    ext.mkdir()
    receipt = ext / ("a" * 64 + ".json")
    receipt.write_text(json.dumps({"observed": {
        "status": "measured", "phase": "decode",
        "source_identity": {"path": str(raw), "size_bytes": raw.stat().st_size, "sha256": sha},
        "forwards": [{"body": {"start_ns": 1, "end_ns": 2}}]}}), encoding="utf-8")
    monkeypatch.setenv("MINDIE_RECEIPT_ROOTS", str(ext))
    discovery.clear_discovery_cache()
    found = discovery.lookup_source_receipt(source_path=raw)
    assert found["status"] == "resolved"
    assert found["receipt"] == str(receipt)
    assert found["source_sha256"] == sha
    # SHA fallback works without the original mount path
    by_sha = discovery.lookup_source_receipt(source_sha256=sha, source_size_bytes=raw.stat().st_size)
    assert by_sha["status"] == "resolved" and by_sha["source_sha256"] == sha
    discovery.clear_discovery_cache()


def test_marker_identity_mutations_do_not_yield_measured_calls(tmp_path: Path) -> None:
    header = "Device_id,Name,Type,Accelerator Core,Start Time(us),Duration(us),Input Shapes\n"
    rows = [
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "0", "1", "10000"),
        ("0", "MatMulV3", "N/A", "N/A", "2", "5", "N/A"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "10", "1", "30000"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "20", "1", "10001"),
        ("0", "MatMulV3", "N/A", "N/A", "22", "6", "N/A"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "30", "1", "30001"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "40", "1", "10002"),
        ("0", "MatMulV3", "N/A", "N/A", "42", "7", "N/A"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "50", "1", "30002"),
    ]
    path = tmp_path / "kernel_details.csv"
    path.write_text(header + "".join(",".join(r) + "\n" for r in rows), encoding="utf-8")
    assert calls.parse_native_calls(path)["status"] == "measured"
    bad = list(rows)
    bad[0] = ("0", "MatMulV3", "N/A", "N/A", "0", "1", "10000")
    path.write_text(header + "".join(",".join(r) + "\n" for r in bad), encoding="utf-8")
    assert calls.parse_native_calls(path)["status"] == "invalid"
    missing = list(rows[1:])
    path.write_text(header + "".join(",".join(r) + "\n" for r in missing), encoding="utf-8")
    partial = calls.parse_native_calls(path)
    assert partial["status"] == "partial" and partial["missing_rep_ids"] == [0]
    assert [c["rep_id"] for c in partial["calls"]] == [1, 2]


def test_native_phase_uses_source_operation_vocabulary() -> None:
    assert calls.native_phase_for_path("/raw/profiler/fia_chunked_q8192/kernel_details.csv")[0] == "prefill"
    assert calls.native_phase_for_path("/raw/profiler/conv1d_T8192/kernel_details.csv")[0] == "prefill"
    assert calls.native_phase_for_path("/raw/profiler/fia_decode_kv8192/kernel_details.csv")[0] == "decode"
    assert calls.native_phase_for_path("/raw/prof/moe/test7/kernel_details.csv")[0] is None


def test_native_owner_join_uses_exact_device_and_ns_bounds(tmp_path: Path) -> None:
    header = "Device_id,Name,Type,Accelerator Core,Start Time(us),Duration(us),Input Shapes\n"
    rows, tasks = [], ["Device_id,kernel_name,kernel_type,stream_id,task_id,task_time(us),task_start(us),task_stop(us)\n"]
    for rep in range(3):
        base = rep * 100
        rows += [("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", str(base), "1", str(10000 + rep)),
                 ("0", "MoeInitRoutingV3", "N/A", "N/A", str(base + 5), "2", "N/A"),
                 ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", str(base + 10), "1", str(30000 + rep))]
        tasks.append(f"0,MoeInitRoutingV3,KERNEL_MIX_AIV,s1,{rep},2,{base + 5},{base + 7}\n")
    path = tmp_path / "kernel_details.csv"
    path.write_text(header + "".join(",".join(r) + "\n" for r in rows), encoding="utf-8")
    (tmp_path / "task_time.csv").write_text("".join(tasks), encoding="utf-8")
    scope = calls.parse_native_calls(path, capture_id="cal")
    assert scope["status"] == "measured" and scope["native_owners"]["owner_counts"] == {"KERNEL_MIX_AIV": 3}
    assert scope["native_owners"]["joined_kernels"] == 3
    assert all(k["native_owner"] == "KERNEL_MIX_AIV" for k in scope["kernel_owners"])


def test_empty_private_segment_is_explicit_missing_rep(tmp_path: Path) -> None:
    header = "Device_id,Name,Type,Accelerator Core,Start Time(us),Duration(us),Input Shapes\n"
    rows = [
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "0", "1", "10000"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "10", "1", "30000"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "20", "1", "10001"),
        ("0", "MatMulV3", "N/A", "N/A", "22", "5", "N/A"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "30", "1", "30001"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "40", "1", "10002"),
        ("0", "MatMulV3", "N/A", "N/A", "42", "6", "N/A"),
        ("0", "aclnnInplaceZero_ZerosLike", "N/A", "N/A", "50", "1", "30002"),
    ]
    path = tmp_path / "kernel_details.csv"
    path.write_text(header + "".join(",".join(r) + "\n" for r in rows), encoding="utf-8")
    out = calls.parse_native_calls(path, capture_id="cal")
    assert out["status"] == "partial"
    assert out["missing_rep_ids"] == [0]
    assert [c["rep_id"] for c in out["calls"]] == [1, 2]
    assert [c["call_id"] for c in out["calls"]] == ["cal:call1", "cal:call2"]


def test_discovery_preserves_conflicting_receipt_digests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw.csv"
    raw.write_text("raw", encoding="utf-8")
    ext = tmp_path / "ext"
    ext.mkdir()
    for index, sha in enumerate(("a" * 64, "b" * 64)):
        (ext / (str(index) * 64 + ".json")).write_text(json.dumps({"observed": {
            "status": "measured", "phase": "decode",
            "source_identity": {"path": str(raw), "size_bytes": 3, "sha256": sha},
            "forwards": []}}), encoding="utf-8")
    monkeypatch.setenv("MINDIE_RECEIPT_ROOTS", str(ext))
    discovery.clear_discovery_cache()
    found = discovery.lookup_source_receipt(source_path=raw)
    assert found["status"] == "conflict"
    assert {item["source_sha256"] for item in found["candidates"]} == {"a" * 64, "b" * 64}
    discovery.clear_discovery_cache()


def test_same_size_mtime_does_not_alias_content(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text("AAAA", encoding="utf-8")
    second.write_text("BBBB", encoding="utf-8")
    st = first.stat()
    import os
    os.utime(second, ns=(st.st_atime_ns, st.st_mtime_ns))
    same_capture, same_artifact = artifacts._same_source(tmp_path, first, second, None)
    assert same_capture is True
    assert same_artifact is False


def test_measurement_json_single_output_proves_no_decode(tmp_path: Path) -> None:
    path = tmp_path / "cell.json"
    path.write_text(json.dumps({"n_requests": 2, "completion_tokens": 2, "ttft_mean_s": 0.8836,
                                "streams": [{"ok": True, "completion_tokens": 1, "ttft_s": 0.8836},
                                            {"ok": True, "completion_tokens": 1, "ttft_s": 0.8836}]}),
                    encoding="utf-8")
    client = artifacts._client_from_measurement_json(path)
    assert client["decode_token_count"] == 2
    assert client["decode_evidence"] == "no_decode_tokens"


def test_inventory_counts_and_no_predictor_import() -> None:
    for name in ("fleet_capture_observations.py", "fleet_capture_artifacts.py"):
        text = (_STRUCT_DIR / name).read_text(encoding="utf-8")
        assert "import fleet_operator_modeling" not in text
        assert "from fleet_operator_modeling" not in text
        assert "import mindie_sim" not in text
