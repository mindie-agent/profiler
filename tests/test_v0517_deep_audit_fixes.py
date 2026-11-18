"""Focused regressions for the v0.5.17 coordinator-filtered deep audit.

Covers Seam 5A (profiler <-> sim SSOT, efficiency attribution, native
prediction) and Seam 5B (collection receipts, bounded source reads, trace/SQL
honesty, aclgraph accounting).  All work is in-memory or tempfile scoped.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from mindie_profiler import collect
from mindie_profiler.aclgraph_multistream import ParallelRegion, diagnose_region
from mindie_profiler.advisor_rules_scanners import _canon_op_token
from mindie_profiler.classify import classify_event
from mindie_profiler.collect import (
    ProfileController, ProfileWindowInjection, post_profile_action,
)
from mindie_profiler.events import ProfilerQueryError, ProfilerUsageError
from mindie_profiler.native_tensor_abi import native_abi_from_slots
from mindie_profiler.segment import (
    discover_rank_sources, is_capture_db_name, load_steps_file,
)
from mindie_profiler.sim_bridge_catalog import _resolve_hw_token
from mindie_profiler.sim_structure_ingress import (
    _case_document, _case_hardware_peaks, _export_structure, _graph_declared,
    resolve_case_geometry, subgraph_efficiency_summary,
)
from mindie_profiler.sql import open_readonly, string_ids_map
from mindie_profiler.sources_trace import build_trace_index, query_trace_events
from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.wait_provenance import WaitOverlapIndex


# ---------------------------------------------------------------- Seam 5A
def test_qualified_sku_beats_family_alias_and_unknown_stays_unknown(monkeypatch):
    import mindie_sim.compose as compose

    monkeypatch.setattr(
        compose, "resolve_hardware_sku",
        lambda raw: "Ascend950PR_958b"
        if raw == "Ascend950PR_958b" else (_ for _ in ()).throw(
            ValueError(f"unknown_hardware_sku:{raw}")))
    assert _resolve_hw_token("Ascend950PR_958b", strict=True) == "Ascend950PR_958b"
    assert _resolve_hw_token("950PR", strict=True) == "Ascend950PR_9579"
    with pytest.raises(ProfilerUsageError, match="unsupported or unrecognized"):
        _resolve_hw_token("Ascend950PR_9999", strict=True)


def _matmul_request():
    abi = native_abi_from_slots(
        "aclnnMatmul",
        [{"shape": [2, 4, 8], "dtype": "bf16", "layout": "ND"},
         {"shape": [2, 8, 16], "dtype": "bf16", "layout": "ND"}],
        [{"shape": [2, 4, 16], "dtype": "bf16", "layout": "ND"}],
    )
    return {
        "request_id": "matmul",
        "api": {"namespace": "aclnn", "entry": "aclnnMatmul",
                "aclnn_symbol": "aclnnMatmul"},
        "version": {"api": "cann-9.2.0"},
        "attrs": {},
        "abi": abi,
        "conditions": {"variant": "dense_matmul",
                       "sequence_rows": "shard", "sequence_ranks": 2},
    }


def test_native_predict_accepts_short_aliases_and_supplied_execution():
    pytest.importorskip("mindie_sim")
    from mindie_sim.backends import materialize
    from mindie_sim.public import ExecutionEnvironment
    from mindie_sim.schema.hardware import Hardware

    from mindie_profiler.sim_bridge import predict_native_requests

    request = _matmul_request()
    durations = [
        predict_native_requests([request], hardware=alias)["predictions"][0]
        for alias in ("950PR", "950DT")
    ]
    assert all(row["status"] == "modeled" and row["duration_ms"] > 0
               for row in durations)

    machine = Hardware.from_mapping(materialize(
        {"backend": "ascend", "sku": "Ascend950PR_9579", "num_devices": 1}))
    fired = []
    execution = ExecutionEnvironment.from_hardware(machine).execution(
        on_operator=lambda *args, **kwargs: fired.append(args))
    out = predict_native_requests(
        [request], execution=execution, blocking=False)
    row = out["predictions"][0]
    assert row["status"] == "modeled_work_only"
    assert row["duration_ms"] is None
    assert row["submitted"] is True
    assert row["actual_execution"]["completion_pending"] is True
    assert execution.engine.summary()["advance_calls"] == 0
    assert out["execution"]["submitted"] == 1
    out = predict_native_requests(
        [request], execution=execution, blocking=True)
    row = out["predictions"][0]
    assert row["status"] == "modeled" and row["duration_ms"] > 0
    assert row["submitted"] is True
    assert execution.engine.summary()["advance_calls"] == 1
    assert out["execution"]["submitted"] == 1
    assert len(fired) == 2


def test_predict_cell_failure_is_not_a_formal_zero_timing_point(
        monkeypatch, tmp_path):
    from mindie_profiler import sim_bridge_cells as cells

    case = tmp_path / "case.json"
    case.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        cells, "raw_case_for_cell",
        lambda _spec: (_ for _ in ()).throw(RuntimeError("unmodeled")))
    result = cells.predict_cell(cells.CellSpec(model_case=case))
    assert result["formal_point"] is False
    assert result["body_ms"] is None
    assert result["prefill_body_ms"] is None
    assert result["decode_body_ms"] is None
    assert result["error"]["code"] == "canonical_predict_error"


def test_cann921_attention_names_and_fused_advisor_tokens():
    names = (
        "KeyPool", "PoolKeyIndexer", "aclnnIndexerQuantCache",
        "aclnnKvCompressEpilog", "aclnnScatterPaKvCache",
        "aclnnDynamicBlockQuant", "aclnnCompressor",
        "aclnnMixedQuantSparseFlashMla", "MixedQuantSparseFlashMla",
        "aclnnMlaPrologV4WeightNz", "InplacePartialRotaryMul",
    )
    for name in names:
        assert classify_event(name=name, op_type=name).block == "Attention", name
    assert classify_event(name="aclnnMhcPreSinkhorn").block != "Unclassified"
    assert _canon_op_token("MoeGatingTopK", "MoeGatingTopK") == "FusedMoeGatingTopK"
    assert _canon_op_token("aclnnScatterPaKvCache", "aclnnScatterPaKvCache") == "FusedCacheEpilog"
    assert _canon_op_token("aclnnKvCompressEpilog", "aclnnKvCompressEpilog") == "FusedCacheEpilog"
    assert _canon_op_token("aclnnIndexerQuantCache", "aclnnIndexerQuantCache") == "FusedCacheEpilog"


def test_case_accepts_three_required_keys_and_propagates_draft_prepare(monkeypatch):
    raw = {"machine": {}, "model": {}, "runtime": {}}
    assert set(_case_document(raw)) == {"machine", "model", "runtime"}

    declared = _graph_declared(
        {"draft_prepare": True, "execution": {"phase": "prefill"}})
    assert declared["draft_prepare"] is True

    seen = {}

    def fake_export(case_doc, **kwargs):
        seen.update(kwargs)
        return {"ok": True}

    import mindie_sim.structure as structure

    monkeypatch.setattr(structure, "export_structure", fake_export)
    _export_structure(raw, {
        "phase": "prefill", "tokens": 4, "context": 0, "sequences": 1,
        "scope": "model", "draft_prepare": True})
    assert seen["draft_prepare"] is True


def test_resolve_case_geometry_keeps_draft_prepare():
    case = pytest.importorskip("mindie_sim.compose").compose_case(
        "deepseek-v3.2", "a3", tp=8, prompt_tokens=64, output_tokens=4, layers=2)
    _parsed, geometry = resolve_case_geometry(
        case, phase="prefill", tokens=4, sequences=1, context=0,
        declared={"draft_prepare": True})
    assert geometry["draft_prepare"] is True


def _structure_and_groups():
    compose_case = pytest.importorskip("mindie_sim.compose").compose_case
    export_structure = pytest.importorskip("mindie_sim.structure").export_structure
    case = compose_case(
        "deepseek-v3.2", "a3", tp=8, prompt_tokens=64, output_tokens=4, layers=2)
    structure = export_structure(
        case, phase="prefill", tokens=64, context=0, sequences=1, scope="body")
    groups = [group for group in structure["subgraphs"]
              if isinstance(group.get("math_summary"), dict)]
    return case, structure, groups


def test_ambiguous_cohort_is_not_evaluated_and_all_windows_are_kept():
    case, structure, groups = _structure_and_groups()
    first, second = groups[0], groups[1]
    mapping = {"windows": [
        {"cohorts": [{
            "target_ids": [first["subgraph_id"], second["subgraph_id"]],
            "busy_union_ns": 1000, "complete_event_count": 2,
            "status_counts": {"candidate": 2},
        }]},
        {"cohorts": [{
            "target_ids": [first["subgraph_id"]], "busy_union_ns": 2000,
            "complete_event_count": 2, "status_counts": {"bound": 2},
            "busy_union_basis": "complete_events_only",
        }]},
        {"cohorts": [{
            "target_ids": [first["subgraph_id"]], "busy_union_ns": 3000,
            "complete_event_count": 2, "status_counts": {"bound": 2},
            "busy_union_basis": "complete_events_only",
        }]},
    ]}
    summary = subgraph_efficiency_summary(structure, mapping, case_doc=case)
    evaluated = next(row for row in summary["records"]
                     if row["subgraph_id"] == first["subgraph_id"])
    ambiguous = next(row for row in summary["records"]
                     if row["subgraph_id"] == second["subgraph_id"])
    assert evaluated["status"] == "evaluated"
    assert evaluated["metrics"] is None
    assert [item["duration_ns"] for item in evaluated["evaluations"]] == [2000.0, 3000.0]
    assert evaluated["candidates"]
    assert ambiguous["status"] == "declared_only"
    assert ambiguous["reason"] == "ambiguous_candidate_set_unbound"


def test_stage_peaks_are_used_and_unresolved_placement_is_unscored():
    compose_case = pytest.importorskip("mindie_sim.compose").compose_case
    export_structure = pytest.importorskip("mindie_sim.structure").export_structure
    from mindie_sim.subgraph_math import (
        SubgraphMathSummary, evaluate_subgraph_efficiency,
    )

    raw = compose_case(
        "deepseek-v3.2", "a3", tp=8, pp=2, prompt_tokens=64,
        output_tokens=4, layers=4)
    machine = dict(raw["machine"])
    device = machine.pop("device")
    devices = []
    for rank in range(machine["num_devices"]):
        row = dict(device)
        rates = dict(row["rates"])
        rates["hbm"] = 1.2e12 if rank < 8 else 0.6e12
        row.update(rates=rates, rank=rank)
        devices.append(row)
    machine["devices"] = devices
    raw["machine"] = machine
    structure = export_structure(
        raw, phase="prefill", tokens=64, context=0, sequences=1, scope="body")
    group = next(item for item in structure["subgraphs"]
                 if item.get("stage") == 1 and isinstance(item.get("math_summary"), dict))
    mapping = {"windows": [{"cohorts": [{
        "target_ids": [group["subgraph_id"]], "busy_union_ns": 1_335_634,
        "complete_event_count": 1, "status_counts": {"bound": 1},
        "busy_union_basis": "complete_events_only",
    }]}]}
    summary = subgraph_efficiency_summary(structure, mapping, case_doc=raw)
    record = next(row for row in summary["records"]
                  if row["subgraph_id"] == group["subgraph_id"])
    expected_peaks = _case_hardware_peaks(raw, replica=0, stage=1)
    fields = {key: value for key, value in group["math_summary"].items()
              if key in SubgraphMathSummary.__dataclass_fields__}
    expected = evaluate_subgraph_efficiency(
        SubgraphMathSummary(**fields), duration_s=1_335_634 / 1e9,
        hardware_peaks=expected_peaks, observed_hbm_bytes=None, invocations=1)
    assert expected_peaks["hbm_peak_bytes_per_s"] == 0.6e12
    assert _case_hardware_peaks(raw, replica=0, stage=None) is None
    assert record["metrics"]["realized_mbu"] == pytest.approx(
        expected["realized_mbu"])


def test_busy_union_uses_complete_events_only():
    target = "rank:0/subgraph:s0"
    row = {
        "physical_signature": "sig", "physical_work": {"hbm_bytes": 10},
        "contract": {"shape": [1]}, "replica": 0, "stage": 0,
        "phase": "decode", "layer": 0, "layer_ids": [0],
        "coverage": {"kind": "complete_subgraph"},
    }

    class Targets:
        all = {target: row}
        subgraphs = {target}

        @staticmethod
        def classify(_ids):
            return {"common": {}}

        @staticmethod
        def members(_item):
            return {_item}

    class Event:
        op_type = "MatMul"
        device_id = "0"
        rank_id = "rank_0"
        start_ns = 100
        end_ns = 200

        def complete_in(self, start_ns, end_ns):
            return self.start_ns >= start_ns and self.end_ns <= end_ns

    observation = SimpleNamespace(
        rank_id="rank_0", window=SimpleNamespace(start_ns=50, end_ns=400))
    accumulator = CohortAccumulator("g", Targets(), observation)
    accumulator.add(
        Event(), (0, 100), status="bound", ids=[target], candidates=[target],
        basis="tensor_contract_only", contract={"shape": [1]})
    clipped = Event()
    clipped.start_ns, clipped.end_ns = -50, 50
    accumulator.add(
        clipped, (-50, 50), status="bound", ids=[target], candidates=[target],
        basis="tensor_contract_only", contract={"shape": [1]})
    [record] = accumulator.finish()
    assert record["complete_event_count"] == 1
    assert record["clipped_event_count"] == 1
    assert record["busy_union_ns"] == 100
    assert record["all_event_busy_union_ns"] == 150
    assert record["busy_union_basis"] == "complete_events_only"


# ---------------------------------------------------------------- Seam 5B
def test_receipt_state_is_restored_before_persist_and_stop_is_sent(
        monkeypatch, tmp_path):
    receipt = tmp_path / "receipt.json"
    injection = ProfileWindowInjection(
        enabled=True, framework="vllm", profiler="torch", profile_dir="/tmp/p",
        endpoint="http://127.0.0.1:9", execution_id="exec", source="cli")
    controller = ProfileController(injection, receipt_path=receipt)
    controller.state = "open"
    controller.actions = [{"action": "start_profile", "status": "ok"}]
    controller._persist()

    restored = ProfileController.from_receipt(receipt)
    assert restored.state == "open"
    assert json.loads(receipt.read_text())["state"] == "open"

    calls = []

    def fake_action(endpoint, action, **kwargs):
        calls.append(action)
        return {"action": action, "status": "ok",
                "endpoint": endpoint, "execution_id": kwargs["execution_id"]}

    monkeypatch.setattr(collect, "post_profile_action", fake_action)
    assert collect.main([
        "--endpoint", injection.endpoint, "--execution-id", "exec",
        "--profile-dir", "/tmp/p", "--action", "stop_profile",
        "--receipt", str(receipt)]) == 0
    assert calls == ["stop_profile"]


def test_receipt_mismatch_is_explicit(tmp_path):
    receipt = tmp_path / "receipt.json"
    controller = ProfileController(
        ProfileWindowInjection(
            enabled=True, framework="vllm", profiler="torch",
            profile_dir="/tmp/p", endpoint="http://127.0.0.1:9",
            execution_id="exec", source="cli"),
        receipt_path=receipt)
    controller.state = "open"
    controller._persist()
    with pytest.raises(ProfilerUsageError, match="receipt does not match"):
        collect.main([
            "--endpoint", "http://127.0.0.1:9", "--execution-id", "other",
            "--profile-dir", "/tmp/p", "--action", "stop_profile",
            "--receipt", str(receipt)])


def test_lost_response_after_send_is_unknown(monkeypatch):
    import http.client

    class Aborted:
        def __init__(self, *_args, **_kwargs):
            pass

        def connect(self):
            pass

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            raise ConnectionAbortedError("peer closed after request")

        def close(self):
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", Aborted)
    result = post_profile_action(
        "http://127.0.0.1:9", "start_profile", execution_id="exec", timeout=1)
    assert result["status"] == "unknown"
    assert result["sent"] is True
    assert result["external_effect"] == "unknown"
    assert result["error"]["code"] == "response_lost"
    assert result["reconcile"]["request_id"] == result["request_id"]


def test_msprof_db_discovery_and_explicit_trace_rejection(tmp_path):
    assert is_capture_db_name("ascend_pytorch_profiler_0.db")
    assert is_capture_db_name("msprof_20260427201914.db")
    assert not is_capture_db_name("msprof_20260427201914.db-wal")
    assert not is_capture_db_name("ascend_pytorch_profiler_index.db")

    rank = tmp_path / "rank0"
    rank.mkdir()
    sqlite3.connect(rank / "msprof_20260427201914.db").close()
    sources = discover_rank_sources(tmp_path)
    assert sources and Path(sources[0].db_path).name == "msprof_20260427201914.db"

    trace = tmp_path / "trace_view.json"
    trace.write_text("[]", encoding="utf-8")
    with pytest.raises(ProfilerUsageError, match="trace subcommands"):
        discover_rank_sources(trace)


def test_steps_file_preserves_decimal_microsecond_boundaries(tmp_path):
    steps = tmp_path / "steps.json"
    steps.write_text(
        '{"steps":[{"step":1,"start_us":1794498607945364.529,'
        '"end_us":1794498607945365.529}]}', encoding="utf-8")
    window = load_steps_file(steps)[0]
    assert window.start_ns == 1794498607945364529
    assert window.end_ns == 1794498607945365529


def test_trace_points_and_numeric_string_ts_survive_the_index(tmp_path):
    trace = tmp_path / "trace_view.json"
    trace.write_text(json.dumps([
        {"name": "flow_start", "ph": "s", "ts": "1763456164889915.460",
         "pid": 1, "tid": 2},
        {"name": "flow_end", "ph": "f", "ts": "1763456164890000.000",
         "pid": 1, "tid": 2},
        {"name": "kernel", "ph": "X", "ts": 1763456164889915.460,
         "dur": 10, "pid": 1, "tid": 2},
    ]), encoding="utf-8")
    index = build_trace_index(trace)["index_path"]
    rows = query_trace_events(
        index, start_ns=1763456164889915460,
        end_ns=1763456164890000001, limit=10)
    assert [row["name"] for row in rows] == ["flow_start", "kernel", "flow_end"]
    assert rows[0]["ts"] is not None and rows[0]["end_ns"] is None
    assert rows[2]["ts"] is not None


def test_sql_interrupt_is_not_an_empty_string_map():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT)")
    con.executemany(
        "INSERT INTO STRING_IDS(id,value) VALUES(?,?)",
        [(index, "x" * 128) for index in range(200_000)])
    con.set_progress_handler(lambda: 1, 1000)
    with pytest.raises(sqlite3.OperationalError, match="interrupted"):
        string_ids_map(con)
    con.close()


def test_sealed_db_retries_with_immutable_open(monkeypatch, tmp_path):
    db = tmp_path / "analysis.db"
    sqlite3.connect(db).close()
    calls = []
    real_connect = sqlite3.connect

    def fake_connect(database, **kwargs):
        calls.append(database)
        if len(calls) == 1:
            raise sqlite3.OperationalError("unable to open database file")
        return real_connect(":memory:")

    monkeypatch.setattr(sqlite3, "connect", fake_connect)
    con = open_readonly(db)
    con.close()
    assert len(calls) == 2 and "immutable=1" in calls[1]


def test_wait_overlap_index_reads_incoming_correlations():
    scope = {"observation_id": "obs", "window_start_ns": 0,
             "window_end_ns": 1_000_000, "step": 1, "rank": "rank_0",
             "device_id": "2", "stream_id": 7}
    anchor = SimpleNamespace(
        event_id="anchor", start_us=100.0, end_us=200.0,
        related_event_ids=(), **scope)
    peer = SimpleNamespace(
        event_id="peer", start_us=100.0, end_us=200.0,
        related_event_ids=("anchor",),
        **{**scope, "stream_id": 8})
    index = WaitOverlapIndex([anchor, peer])
    found = index.find(anchor, (100.0, 200.0), min_overlap_ratio=0.5)
    assert found is not None and found[0] is peer and found[2] == 100_000


def test_zero_duration_join_after_idle_gap_keeps_true_overlap():
    def node(identifier, stream, start, duration, deps=()):
        return {"id": identifier, "stream_id": stream, "duration_us": duration,
                "start_us": start, "dependencies": list(deps)}

    for join_at in (10, 30):
        region = ParallelRegion("r", nodes=(
            node("a", 0, 0, 10), node("b", 1, 0, 10), node("c", 2, 0, 10),
            node("join", 0, join_at, 0, ("a", "b", "c")),
        ), event_pairs=1, graph_mode="full")
        diagnostic = diagnose_region(region)
        assert diagnostic.code == "OK"
        assert diagnostic.overlap_pct == 100.0


def test_aclgraph_cli_exits_nonzero_on_failed_tool(capsys):
    from mindie_profiler.aclgraph_mcp import main

    assert main([
        "--tool", "aclgraph_diagnose",
        "--args-json", '{"region": {"nodes": []}}']) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] == 0 and payload["err"] == "EREGION"


def test_native_capture_caps_cold_shim_build_to_remaining_budget(monkeypatch):
    from mindie_profiler import native_capture

    seen = {}

    monkeypatch.setattr(native_capture, "discover_cann9", lambda _root: object())

    def fake_shim(_install, **kwargs):
        seen.update(kwargs)
        raise RuntimeError("shim stop")

    monkeypatch.setattr(native_capture, "ensure_capture_shim_binary", fake_shim)
    with pytest.raises(RuntimeError, match="shim stop"):
        native_capture.capture_profile(
            command=["true"], warmup_timeout_s=0.01, capture_timeout_s=0.01,
            export_timeout_s=0.0, cleanup_grace_s=0.02, outer_timeout_s=0.05)
    assert 0 < seen["timeout_s"] <= 0.05


# ------------------------------------------------- Round-2 final audit closure
def test_compact_ascend_sku_normalizes_before_qualified_lookup():
    from mindie_profiler.sim_bridge_catalog import _detect_hardware
    from mindie_sim.backends.ascend import profiles

    expected = {
        "Ascend9109362": "Ascend910_9362",
        "Ascend9109382": "Ascend910_9382",
        "Ascend9109392": "Ascend910_9392",
        "Ascend950PR9579": "Ascend950PR_9579",
    }
    for compact, sku in expected.items():
        assert _resolve_hw_token(compact, strict=False) == sku
        assert _resolve_hw_token(compact, strict=True) == sku
    assert profiles()["Ascend910_9362"]["device"]["rates"]["hbm"] == 1.2e12
    assert _detect_hardware(
        None, {"host": "Ascend9109362"}, {}, {}, {}, None,
        []) == "Ascend910_9362"
    assert _detect_hardware(
        "Ascend9109362", {}, {}, {}, {}, None, []) == "Ascend910_9362"
    with pytest.raises(ProfilerUsageError, match="unsupported or unrecognized"):
        _resolve_hw_token("Ascend9109999", strict=True)


def test_draft_prepare_export_never_falls_back_to_target_only(monkeypatch):
    import mindie_sim.structure as structure

    calls = []

    def fake_export(case_doc, **kwargs):
        calls.append(kwargs)
        if kwargs.get("draft_prepare"):
            raise TypeError(
                "export_structure() got an unexpected keyword argument "
                "'draft_prepare'")
        return {"target_only": True}

    monkeypatch.setattr(structure, "export_structure", fake_export)
    with pytest.raises(ProfilerUsageError, match="cannot regenerate draft_prepare"):
        _export_structure({"machine": {}, "model": {}, "runtime": {}}, {
            "phase": "prefill", "tokens": 4, "context": 0, "sequences": 1,
            "scope": "model", "draft_prepare": True})
    assert len(calls) == 1 and calls[0]["draft_prepare"] is True


def test_draft_prepare_ingress_reports_unsupported_geometry():
    from mindie_profiler.sim_structure_ingress import apply_structure_ingress

    compose_case = pytest.importorskip("mindie_sim.compose").compose_case
    case = compose_case(
        "deepseek-v3.2", "a3", tp=8, prompt_tokens=64, output_tokens=4,
        layers=2)
    graph = {
        "schema": "mindie-sim.graph/1", "graph_scope": "model",
        "tokens_per_sequence": 4, "sequences_per_replica": 1,
        "draft_prepare": True, "duration_ms": 1.097217,
        "bounds": {"combined_ms": 1.2},
    }
    report = {}
    apply_structure_ingress(
        report, [], structure=graph, sim_case=case, phase="prefill", context=0)
    ingress = report["structure_ingress"]
    assert ingress["status"] == "unsupported_geometry"
    assert ingress["draft_prepare"] is True
    assert ingress["generated_structure"] is False
    assert "draft_prepare" in ingress["reason"]
    assert report["sim_cohort_comparison"]["status"] == "unsupported_geometry"
    assert "structure_mapping" not in report
    graph_summary = report["sim_graph_summary_comparison"]
    assert graph_summary["status"] == "unsupported_geometry"
    assert graph_summary["graph_predicted_ms"] == pytest.approx(1.097217)


def test_homogeneous_candidate_cohort_is_scored_once_per_window():
    import copy

    case, structure, groups = _structure_and_groups()
    base = groups[0]
    clones = []
    for index in range(3):
        clone = copy.deepcopy(base)
        clone.update(subgraph_id=f"rank:0/subgraph:hom{index}",
                     replica=0, stage=0)
        # Exported math summaries carry their own identity; it must not make
        # otherwise identical declared work look inhomogeneous.
        clone["math_summary"] = {
            **clone["math_summary"], "subgraph_id": clone["subgraph_id"]}
        clones.append(clone)
    structure = {**structure, "subgraphs": clones}
    cohort = {
        "cohort_id": "homogeneous",
        "target_ids": [row["subgraph_id"] for row in clones],
        "busy_union_ns": 1_335_634,
        "complete_event_count": 1, "status_counts": {"candidate": 3},
    }
    mapping = {"windows": [{"cohorts": [cohort]}]}
    summary = subgraph_efficiency_summary(structure, mapping, case_doc=case)
    assert summary["status"] == "evaluated"
    assert summary["evaluated_count"] == 1
    assert summary["cohort_evaluation_count"] == 1
    [evaluation] = summary["cohort_evaluations"]
    assert evaluation["candidates"] == [row["subgraph_id"] for row in clones]
    assert evaluation["occurrence_binding"] == "candidate_cohort_only"
    assert evaluation["metrics"]["realized_mbu"] is not None
    assert all(row["status"] == "declared_only" and row["evaluations"] == []
               for row in summary["records"])
    assert all(row["reason"] == "occurrence_unbound_scored_once_at_cohort_level"
               for row in summary["records"])

    # Different declared work is not homogeneous: no candidate is priced.
    drifted = dict(clones[2]["math_summary"])
    drifted["realized_hbm_bytes"] = float(drifted["realized_hbm_bytes"]) + 1.0
    clones[2]["math_summary"] = drifted
    inhomogeneous = subgraph_efficiency_summary(
        {**structure, "subgraphs": clones}, mapping, case_doc=case)
    assert inhomogeneous["status"] == "structure_only"
    assert inhomogeneous["cohort_evaluations"] == []
    assert inhomogeneous["records"][0]["reason"] == \
        "ambiguous_candidate_set_unbound"


def test_post_send_connection_refused_is_unknown(monkeypatch):
    import http.client

    class RefusedAfterSend:
        def __init__(self, *_args, **_kwargs):
            pass

        def connect(self):
            pass

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            raise ConnectionRefusedError(111, "Connection refused")

        def close(self):
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", RefusedAfterSend)
    result = post_profile_action(
        "http://127.0.0.1:9", "start_profile", execution_id="exec", timeout=1)
    assert result["sent"] is True
    assert result["status"] == "unknown"
    assert result["external_effect"] == "unknown"
    assert result["error"]["code"] == "response_lost"
    assert result["reconcile"]["request_id"] == result["request_id"]


def test_multi_window_pmu_cache_is_released_per_window(tmp_path, monkeypatch):
    from test_profiler_review_r1_contracts import (
        _Ids, _create_db, _insert_pmu, _insert_task,
    )
    from mindie_profiler.events import Window
    from mindie_profiler.sources_db import DbSource, probe_db

    db_path = tmp_path / "multi_window_pmu.db"
    _create_db(db_path, indexed=False)
    con = sqlite3.connect(db_path)
    try:
        ids = _Ids(con)
        _insert_task(con, ids, 1, 1_000, 2_000)
        _insert_task(con, ids, 2, 101_000, 102_000)
        _insert_pmu(con, 1, ids("aic_mac_ratio"), 0.25)
        _insert_pmu(con, 2, ids("aic_mac_ratio"), 0.50)
        con.commit()
    finally:
        con.close()

    source = DbSource(probe_db(db_path))
    windows = [Window(0, 3_000, step=0, label="0"),
               Window(100_000, 103_000, step=1, label="1")]
    cached_ids = []
    real_iter = DbSource.iter_window

    def observed(self, window, **kwargs):
        cached_ids.append(set(self._pmu_cache or {}))
        return real_iter(self, window, **kwargs)

    monkeypatch.setattr(DbSource, "iter_window", observed)
    rows = source.iter_windows(windows, max_rows=500)
    assert cached_ids == [{1}, {2}]
    assert source._pmu_cache is None
    assert [stats.pmu_rows for _events, stats in rows] == [1, 1]


def test_nonblocking_submission_never_advances_caller_engine():
    pytest.importorskip("mindie_sim")
    from mindie_sim.backends import materialize
    from mindie_sim.public import ExecutionEnvironment
    from mindie_sim.schema.hardware import Hardware

    from mindie_profiler.sim_bridge import predict_native_requests

    machine = Hardware.from_mapping(materialize(
        {"backend": "ascend", "sku": "Ascend950PR_9579", "num_devices": 1}))
    execution = ExecutionEnvironment.from_hardware(machine).execution(
        on_operator=lambda *_args, **_kwargs: None)
    out = predict_native_requests(
        [_matmul_request()], execution=execution, blocking=False)
    row = out["predictions"][0]
    assert row["status"] == "modeled_work_only"
    assert row["duration_ms"] is None
    receipt = row["actual_execution"]
    assert receipt["blocking"] is False and receipt["submitted"] is True
    assert receipt["duration_ms"] is None
    assert receipt["completion_pending"] is True
    assert execution.engine.summary()["advance_calls"] == 0


def test_deferred_sqlite_open_probe_retries_immutable(monkeypatch, tmp_path):
    db = tmp_path / "analysis.db"
    db.write_bytes(b"")
    calls = []
    real_connect = sqlite3.connect

    class DeferredFailure:
        def execute(self, _sql):
            raise sqlite3.OperationalError("unable to open database file")

        def close(self):
            pass

    def fake_connect(database, **kwargs):
        calls.append(database)
        if len(calls) == 1:
            return DeferredFailure()
        return real_connect(":memory:")

    monkeypatch.setattr(sqlite3, "connect", fake_connect)
    con = open_readonly(db)
    con.close()
    assert len(calls) == 2 and "immutable=1" in calls[1]

    # A sidecar-bearing DB is not sealed: a deferred open failure must not
    # silently switch to immutable reads.
    calls.clear()
    Path(f"{db.resolve()}-wal").write_bytes(b"")
    with pytest.raises(ProfilerQueryError, match="cannot open profiler db"):
        open_readonly(db)


def test_idle_join_keeps_ok_but_event_wait_consuming_gain_is_a4():
    def node(identifier, stream, start, duration):
        return {"id": identifier, "stream_id": stream,
                "duration_us": duration, "start_us": start}

    events = [{"id": "done_b", "record": "b", "wait": "join"},
              {"id": "done_c", "record": "c", "wait": "join"}]
    for join_at in (30, 31, 40):
        diagnostic = diagnose_region({
            "name": "idle-join", "nodes": [
                node("a", 0, 0, 10), node("b", 1, 0, 10),
                node("c", 2, 0, 10), node("join", 0, join_at, 0),
            ], "events": events,
        })
        assert diagnostic.code == "OK"
        assert diagnostic.overlap_pct == 100.0
        assert diagnostic.details["cross_stream_event_delays_us"] == {}

    eroded = diagnose_region({
        "name": "event-erosion", "nodes": [
            node("a", 0, 0, 10), node("b", 1, 8.5, 10),
            node("join", 0, 9, 0),
        ], "events": [{"id": "done_b", "record": "b", "wait": "join"}],
    })
    assert eroded.code == "A4"
    assert eroded.overlap_pct > 5.0
    assert eroded.net_speedup_us == 0.0
    assert eroded.details["solved_event_delay_us"] > 0.0
    assert eroded.details["event_loss_us"] > 0.0


def test_msprof_db_inside_mindstudio_output_is_a_single_prof_rank(tmp_path):
    rank = tmp_path / "PROF_0"
    mindstudio = rank / "mindstudio_profiler_output"
    mindstudio.mkdir(parents=True)
    sqlite3.connect(mindstudio / "msprof_20260427201914.db").close()

    source, = discover_rank_sources(tmp_path)
    assert Path(source.rank_dir) == rank.resolve()
    assert source.rank_id != "mindstudio_profiler_output"
    assert Path(source.db_path).name == "msprof_20260427201914.db"


def test_worker_warmup_clock_starts_when_session_is_armed(monkeypatch, tmp_path):
    from mindie_profiler import native_capture

    class Clock:
        now = 0.0

        def monotonic(self):
            return self.now

        def sleep(self, seconds):
            self.now += max(float(seconds), 0.01)

    class Session:
        slot_overflow_count = 0
        view = SimpleNamespace(
            header=SimpleNamespace(gear=1, generation=0))

        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def configure_run(self, **_kwargs):
            clock.now = 5.0  # cold C shim compilation preceded the arm
            return 1

        def snapshot_workers(self, **_kwargs):
            snapshots.append(clock.now)
            return []

        def set_phase(self, _phase):
            pass

    clock = Clock()
    snapshots = []
    fake_time = SimpleNamespace(
        monotonic=clock.monotonic, sleep=clock.sleep)
    install = SimpleNamespace(
        libmsprofiler_so="/fake/libmsprofiler.so",
        as_dict=lambda: {"root": "/fake"})
    monkeypatch.setattr(native_capture, "time", fake_time)
    monkeypatch.setattr(native_capture, "discover_cann9", lambda _root: install)
    monkeypatch.setattr(
        native_capture, "ensure_capture_shim_binary",
        lambda _install, **_kwargs: "/fake/shim.so")
    monkeypatch.setattr(
        native_capture, "resolve_shm_backing_path",
        lambda *_args, **_kwargs: tmp_path / "shm")
    monkeypatch.setattr(native_capture, "CaptureShmSession", Session)
    report = native_capture.capture_profile(
        attach_session_id="cap_test", output_dir=tmp_path / "capture",
        warmup_timeout_s=0.5, capture_timeout_s=0.1, export_timeout_s=0.0,
        cleanup_grace_s=0.02, outer_timeout_s=10.0)
    assert any(note.startswith("warmup_timeout_exceeded")
               for note in report["notes"])
    # The pre-arm cold build consumed 5 s; warmup still ran for its full
    # 0.5 s window instead of expiring before the first poll.
    assert max(snapshots) >= 5.4


def test_oversized_pmu_window_streams_instead_of_retaining_raw_rows(
        tmp_path, monkeypatch):
    from test_profiler_review_r1_contracts import (
        _Ids, _create_db, _insert_pmu, _insert_task,
    )
    from mindie_profiler import sources_db
    from mindie_profiler.events import Window
    from mindie_profiler.sources_db import DbSource, probe_db

    db_path = tmp_path / "oversized_pmu.db"
    _create_db(db_path, indexed=False)
    con = sqlite3.connect(db_path)
    try:
        ids = _Ids(con)
        _insert_task(con, ids, 1, 1_000, 2_000)
        _insert_pmu(con, 1, ids("aic_mac_ratio"), 0.25)
        _insert_pmu(con, 1, ids("aic_mte2_ratio"), 0.50)
        con.commit()
    finally:
        con.close()

    monkeypatch.setattr(sources_db, "_PMU_PRIME_ROW_CAP", 1)
    source = DbSource(probe_db(db_path))
    [(events, stats)] = source.iter_windows(
        [Window(0, 3_000, step=0, label="0")], max_rows=500)
    assert source._pmu_cache is None
    assert stats.pmu_rows == 2
    assert events[0].pmu_status == "bound"
    assert dict(events[0].pmu) == {
        "aic_mac_ratio": 0.25, "aic_mte2_ratio": 0.5}


def test_glm_unbound_mla_prolog_layers_are_priced_once_not_per_layer():
    from mindie_profiler.structure_mapping import map_structure
    from mindie_sim.structure import export_structure
    from test_structure_subgraphs import observation, prolog
    from tests.sim_fixtures import case_path

    case = json.loads(case_path("glm53-a3-w4a8.json").read_text())
    case["model"]["layers"] = 4
    case["runtime"]["pp"] = 1
    case["machine"]["num_devices"] = 8
    case["runtime"].setdefault("kernels", {}).setdefault(
        "lowerings", {}).update(mla_prolog="vllm_ascend_mla_prolog_v3")
    structure = export_structure(case, phase="prefill", tokens=4096)
    mapping = map_structure([observation([prolog.__wrapped__()])], structure)
    summary = subgraph_efficiency_summary(structure, mapping, case_doc=case)
    assert summary["status"] == "evaluated"
    [evaluation] = summary["cohort_evaluations"]
    assert len(evaluation["candidates"]) == 3
    from mindie_sim.subgraph_math import (
        SubgraphMathSummary, evaluate_subgraph_efficiency,
    )
    group = next(row for row in structure["subgraphs"]
                 if row["subgraph_id"] == evaluation["candidates"][0])
    fields = {key: value for key, value in group["math_summary"].items()
              if key in SubgraphMathSummary.__dataclass_fields__}
    expected = evaluate_subgraph_efficiency(
        SubgraphMathSummary(**fields), duration_s=1_335_634 / 1e9,
        hardware_peaks=_case_hardware_peaks(case, replica=0, stage=0),
        observed_hbm_bytes=None, invocations=1)
    assert evaluation["metrics"]["realized_mbu"] == pytest.approx(
        expected["realized_mbu"])
    assert evaluation["metrics"]["realized_mbu"] == pytest.approx(
        0.15667, rel=1e-3)
    assert all(row["evaluations"] == [] for row in summary["records"]
               if "mla_prolog" in str(row["subgraph_id"]))


def test_r2_compact_sku_inside_hostname_resolves_exact_profile():
    assert _resolve_hw_token("node-Ascend9109362") == "Ascend910_9362"
    assert _resolve_hw_token("rack04-ascend950pr958b-n1") == "Ascend950PR_958b"


def test_r2_concurrent_iter_windows_share_dbsource_without_pmu_steal(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from test_profiler_review_r1_contracts import (
        _Ids, _create_db, _insert_pmu, _insert_task,
    )
    from mindie_profiler.events import Window
    from mindie_profiler.sources_db import DbSource, probe_db

    db_path = tmp_path / "concurrent_pmu.db"
    _create_db(db_path, indexed=False)
    con = sqlite3.connect(db_path)
    try:
        ids = _Ids(con)
        _insert_task(con, ids, 1, 1_000, 2_000)
        _insert_task(con, ids, 2, 101_000, 102_000)
        _insert_pmu(con, 1, ids("aic_mac_ratio"), 0.25)
        _insert_pmu(con, 2, ids("aic_mac_ratio"), 0.50)
        con.commit()
    finally:
        con.close()

    source = DbSource(probe_db(db_path))
    windows = [Window(0, 3_000, step=0, label="0"),
               Window(100_000, 103_000, step=1, label="1")]
    for _ in range(16):
        with ThreadPoolExecutor(max_workers=4) as pool:
            runs = list(pool.map(
                lambda _: source.iter_windows(windows, max_rows=500), range(4)))
        for batch in runs:
            assert [ev.pmu_status for events, _ in batch for ev in events] == [
                "bound", "bound"
            ]


def test_r2_open_readonly_never_retries_sqlite_busy_as_immutable(tmp_path):
    db = tmp_path / "busy.db"
    writer = sqlite3.connect(db, isolation_level=None)
    try:
        writer.execute("PRAGMA journal_mode = DELETE")
        writer.execute("CREATE TABLE STRING_IDS (id INTEGER PRIMARY KEY, value TEXT)")
        writer.execute("BEGIN EXCLUSIVE")
        writer.execute("CREATE TABLE measurement (value INTEGER)")
        writer.execute("INSERT INTO measurement VALUES (42)")
        with pytest.raises(ProfilerQueryError, match="locked"):
            open_readonly(db, timeout_s=0.1)
        writer.execute("COMMIT")
        reader = open_readonly(db)
        try:
            assert reader.execute("SELECT value FROM measurement").fetchall() == [(42,)]
        finally:
            reader.close()
    finally:
        writer.close()


def test_r2_one_layer_unbound_tensor_contract_never_evaluates_layer_record():
    from mindie_profiler.structure_mapping import map_structure
    from mindie_sim.structure import export_structure
    from test_structure_subgraphs import observation, prolog
    from tests.sim_fixtures import case_path

    case = json.loads(case_path("glm53-a3-w4a8.json").read_text())
    case["model"]["layers"] = 1
    case["runtime"]["pp"] = 1
    case["machine"]["num_devices"] = 8
    case["runtime"].setdefault("kernels", {}).setdefault(
        "lowerings", {}).update(mla_prolog="vllm_ascend_mla_prolog_v3")
    structure = export_structure(case, phase="prefill", tokens=4096)
    mapping = map_structure([observation([prolog.__wrapped__()])], structure)
    summary = subgraph_efficiency_summary(structure, mapping, case_doc=case)
    assert all(row["evaluations"] == [] for row in summary["records"]
               if "mla_prolog" in str(row["subgraph_id"]))
    assert len(summary["cohort_evaluations"]) == 1


def test_r2_cross_stream_event_reversing_parallel_gain_reports_a4():
    eroded = diagnose_region({
        "name": "producer-consumer-reversal",
        "nodes": [
            {"id": "consumer", "stream_id": 0, "start_us": 0.0, "duration_us": 4.0},
            {"id": "producer", "stream_id": 1, "start_us": 2.0, "duration_us": 2.0},
            {"id": "other", "stream_id": 1, "start_us": 4.0, "duration_us": 2.0},
        ],
        "events": [{"id": "ev", "record": "producer", "wait": "consumer"}],
    })
    assert eroded.code == "A4"
    assert eroded.wall_us == pytest.approx(9.5)
    assert eroded.details["potential_gain_us"] == pytest.approx(2.0)


def test_r2_recursive_inventory_discovers_db_only_mindstudio_capture(tmp_path):
    from mindie_profiler.inventory import inventory_profile

    db = tmp_path / "PROF_0" / "mindstudio_profiler_output" / "msprof_1.db"
    db.parent.mkdir(parents=True)
    con = sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE STRING_IDS (id INTEGER PRIMARY KEY, value TEXT)")
        con.execute(
            "CREATE TABLE TASK (globalTaskId INTEGER, startNs INTEGER, endNs INTEGER,"
            " deviceId INTEGER, streamId INTEGER, taskId INTEGER)")
        con.commit()
    finally:
        con.close()
    inv = inventory_profile(tmp_path)
    assert inv["rank_count"] == 1

