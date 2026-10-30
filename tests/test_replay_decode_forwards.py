"""Missing evidence and source mismatches never turn into numerical accuracy."""
import importlib.util
from copy import deepcopy
import json
from pathlib import Path

import pytest

from mindie_profiler.sources_db import sha256_file


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def replay(monkeypatch):
    directory = ROOT / "examples/structure"
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location("decode_forward_replay", directory / "replay_decode_forwards.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_capture_without_body_boundaries_never_predicts(replay, monkeypatch):
    path = ROOT / "tests/fixtures/fusion_contracts/a3_qwen35.csv"

    def forbidden(*args, **kwargs):
        pytest.fail("missing body evidence must not invoke prediction or scan raw events")

    monkeypatch.setattr(replay, "_predict_bounded", forbidden)
    monkeypatch.setattr(replay, "_source", forbidden)
    report = replay.replay_manifest({
        "schema_version": "mindie-decode-forward-replay/1", "cases": [{
            "case_id": "retained-hardware-capture", "source": {"path": str(path), "sha256": sha256_file(path)},
            "boundaries_path": None, "graph_envelopes_path": "separate-graph-diagnostic.json",
            "scenario_evidence": {"target_tpot_ms": 5, "target_prefix_cache_hit_rate": 1},
        }],
    }, base=ROOT)
    row = report["cases"][0]
    assert row["observed"] is row["prediction"] is None
    assert row["comparison"]["observed_ms"]["mean"] is None
    assert row["comparison"]["predicted_ms"] is None
    assert row["comparison"]["passed"] is None
    assert report["summary"] == {"case_count": 1, "source_case_count": 1, "measured_cases": 0, "compared_cases": 0,
                                 "passed_cases": 0, "unresolved_cases": 1, "failed_cases": 0}
    assert "target_body_boundary_evidence_missing" in replay.render(report)


def test_boundary_source_mismatch_is_failed_and_visible(replay, tmp_path, monkeypatch):
    source = ROOT / "tests/fixtures/fusion_contracts/a3_qwen35.csv"
    boundary = tmp_path / "boundaries.json"
    boundary.write_text(json.dumps({"schema_version": "mindie-forward-boundaries/1", "forwards": []}))
    report = replay.replay_manifest({
        "schema_version": "mindie-decode-forward-replay/1", "cases": [{
            "case_id": "source-mismatch", "source": {"path": str(source), "sha256": "0" * 64},
            "boundaries_path": str(boundary),
        }],
    }, base=tmp_path)
    assert report["summary"]["failed_cases"] == 1
    assert report["cases"][0]["error"]["message"] == "forward_capture_source_hash_mismatch"
    assert report["cases"][0]["comparison"]["status"] == "failed"
    assert report["cases"][0]["comparison"]["passed"] is None


def test_geometry_compaction_preserves_separate_layer_populations(replay):
    # Internal aggregate ledger: one q=4 call must not contaminate q=1 means.
    forwards = [{"forward_id": str(index), "status": "measured", "body_forward_span_ms": duration,
                 "geometry": {"tokens_per_sequence": q, "sequences_per_replica": 1}, "stages": []}
                for index, (q, duration) in enumerate(((1, 2), (4, 10), (1, 4)))]
    samples = [{"forward_id": str(index), "status": "measured", "span_ms": duration}
               for index, duration in enumerate((1, 8, 2))]
    report = replay.compact_observation({
        "forwards": forwards, "per_layer_ms": [{"kind": "dense_layer", "layer_id": 0,
                                                  "samples": samples}], "stage_span_ms": [],
    })
    groups = {row["geometry"]["tokens_per_sequence"]: row for row in report["geometry_groups"]}
    assert groups[1]["body_forward_span_ms"]["mean"] == 3
    assert groups[4]["body_forward_span_ms"]["mean"] == 10
    assert groups[1]["per_layer_ms"][0]["stats"]["mean"] == 1.5
    assert groups[4]["per_layer_ms"][0]["stats"]["mean"] == 8
    assert groups[1]["per_layer_ms"][0]["sample_count"] == 2
    assert len(groups[1]["per_layer_ms"][0]["samples"]) == 1


def test_real_mixed_geometry_priority_retains_tail_population(replay):
    directory = ROOT / "examples/structure/acceptance-20261030-expanded"
    manifest = json.loads((directory / "decode-forward-auto-cases.json").read_text())
    declaration = next(row for row in manifest["cases"] if row["case_id"] == "v4flash-a3-tp8-c4")
    observed = json.loads((directory / f"auto-forward-{declaration['case_id']}.json").read_text())
    scenarios = replay._automatic_scenarios(declaration, observed)
    result = {"case_id": declaration["case_id"]}
    replay._compare_scenarios(result, scenarios, None, {}, prediction_timeout_s=1,
                             run_predictions=False, geometry_limit=1)
    rows = result["geometry_cases"]
    assert len(rows) == 2
    assert [row["comparison"]["observed_forward_count"] for row in rows] == [104, 4]
    assert rows[0]["comparison"]["reasons"] == ["prediction_not_requested"]
    assert rows[1]["comparison"]["reasons"] == ["prediction_deferred_by_population_priority"]
    assert sum(row["comparison"]["observed_forward_count"] for row in rows) == observed["body_forward_span_ms"]["count"]
    assert all(row["comparison"]["predicted_ms"] is None for row in rows)


@pytest.mark.parametrize("declaration", ["none", "case", "manifest", "regime_only"])
def test_reused_capture_retains_explicit_calibration_and_service_domains(
        replay, monkeypatch, tmp_path, declaration):
    pytest.importorskip("mindie_sim.prediction.structure")
    directory = ROOT / "examples/structure/acceptance-20261030-qwen35-mc2-tp-bf71bd7d"
    manifest = json.loads((directory / "decode-forward-qwen35-mc2-tp-cases.json").read_text())
    row = next(row for row in manifest["cases"] if row["case_id"].endswith("-c4-graph"))
    if not Path(row["source"]["path"]).is_file() or not Path(row["sim_case_path"]).is_file():
        pytest.skip("requires retained source identity and companion Sim case")
    observed = json.loads(Path(row["extraction_path"]).read_text())
    case = json.loads(Path(row["sim_case_path"]).read_text())
    evidence = {"evaluation_relation": "in_sample", "fit_source_identity": row["source"],
                "evaluation_source_identity": row["source"]}
    rule = {"id": "explicit-copy-service", "match": {"recipe": "tensor_materialization"},
            "coordinates": {"rows": {"path": "local_shape.0"}},
            "domain": {"rows": {"min": 16, "max": 128}},
            "response": {"fixed_us": 3.0, "terms": [{"coordinate": "rows", "us_per_unit": 0.1,
                "scale_with": {"resource": "mte3", "reference_rate": 4000000000000}}]},
            "provenance": {"basis": "test_declaration_transport_only", "source_identity": row["source"]}}
    if declaration != "none":
        case["runtime"].setdefault("kernels", {})["service_regimes"] = [rule]
    if declaration in {"case", "manifest"}:
        case["runtime"].setdefault("metadata", {}).update(
            calibration_origin="explicit_case", calibration_evidence=evidence)
    if declaration == "manifest":
        # Explicit report declaration wins; this tests transport, not whether a
        # purported holdout split is independent (which needs its own evidence).
        row.update(calibration_origin="explicit_manifest", calibration_evidence={
            "evaluation_relation": "heldout", "basis": "declaration_transport_test_only"})
    case_path = tmp_path / "source-case.json"
    case_path.write_text(json.dumps(case))
    row["sim_case_path"] = str(case_path)
    unchanged = deepcopy((row, case, observed))

    def forbidden(*args, **kwargs):
        pytest.fail("retained extraction metadata replay must not scan events or execute a model")

    monkeypatch.setattr(replay, "_source", forbidden)
    monkeypatch.setattr(replay, "_predict_bounded", forbidden)
    result = replay.replay_case(row, ROOT, run_predictions=False)
    geometries = result["geometry_cases"]
    assert sum(item["comparison"]["observed_forward_count"] for item in geometries) == 91
    assert max(item["comparison"]["observed_forward_count"] for item in geometries) == 84
    for item in [result, *geometries]:
        assert item["calibration_origin"] == {
            "case": "explicit_case", "manifest": "explicit_manifest"}.get(declaration, "not_declared")
        if declaration == "none":
            assert item["calibration_evidence"] is None
        else:
            saved = item["calibration_evidence"]
            assert saved["declared_service_regimes"] == [rule]
            assert saved.get("evaluation_relation") == {
                "case": "in_sample", "manifest": "heldout"}.get(declaration)
    assert result["observed"]["geometry_groups"] == observed["geometry_groups"]
    assert (row, case, observed) == unchanged
    assert all(item["prediction"] is None for item in geometries)


def test_prediction_worker_has_bounded_receipt_and_reuses_completed_geometry(replay, monkeypatch, tmp_path):
    sim = pytest.importorskip("mindie_sim.prediction.body")
    path = Path(sim.__file__).resolve().parents[2] / "examples/quickstart.json"
    if not path.is_file():
        pytest.skip("Sim source example is required for the worker contract")
    geometry = {"phase": "decode", "tokens_per_sequence": 1,
                "context_tokens": 16, "sequences_per_replica": 1}
    cache = replay.PredictionCache(tmp_path / "predictions")
    first = replay._predict_bounded(path, geometry, cache, timeout_s=10)
    assert first["status"] == "completed"
    assert first["execution"]["peak_rss_bytes"] <= 512 * 1024 ** 2
    assert first["runtime_identity"]["sources_unchanged"]

    def duplicate(*args, **kwargs):
        pytest.fail("identical completed case geometry must not start another worker")

    monkeypatch.setattr(replay.subprocess, "run", duplicate)
    second = replay._predict_bounded(path, geometry,
                                     replay.PredictionCache(tmp_path / "predictions"), timeout_s=10)
    assert second["reused_prediction"]
    assert second["prediction"] == first["prediction"]


def test_real_high_concurrency_activity_preserves_union_and_layer_populations(replay):
    directory = ROOT / "examples/structure/acceptance-20261030-high-concurrency"
    observed = json.loads((directory / "auto-forward-a5_qwen36_highconc_c40.json").read_text())
    manifest = json.loads((directory / "decode-forward-auto-cases.json").read_text())
    declaration = next(row for row in manifest["cases"] if row["case_id"] == "a5_qwen36_highconc_c40")
    scenario, = replay._automatic_scenarios(declaration, observed)
    projected = scenario["observed"]
    assert projected["body_activity_ms"] == observed["body_activity_ms"]
    assert projected["body_internal_gap_ms"] == observed["body_internal_gap_ms"]
    assert projected["body_activity_ms"]["mean"] + projected["body_internal_gap_ms"]["mean"] == pytest.approx(
        projected["body_forward_span_ms"]["mean"])
    # This retained capture has overlapping HCOM/compute stream intervals.
    forward = observed["forwards"][0]
    assert sum(row["activity_union_ms"] for row in forward["per_stream_activity_ms"]) > forward["body_activity_ms"]
    assert forward["body_activity_ms"] + forward["body_internal_gap_ms"] == pytest.approx(
        (forward["end_ns"] - forward["start_ns"]) / 1e6)
    report = json.loads((directory / "decode-forward-replay.json").read_text())
    predicted = next(row["prediction"] for row in report["cases"]
                     if row["source_case_id"] == declaration["case_id"])
    layers = replay.compare_layers(predicted, projected)
    assert layers["summary"]["compared_layers"] == 64
    for group in layers["attention_kind_distributions"]:
        assert group["observed_ms"]["count"] == {"gdn": 48, "gqa": 16}[group["attention_kind"]]
        assert group["observed_activity_ms"]["mean"] + group["observed_internal_gap_ms"]["mean"] == pytest.approx(
            group["observed_ms"]["mean"])
    steady = layers["steady_layer_comparison"]
    assert not steady["body_span_modified"]
    assert steady["population"]["layer_count"] == 63
    assert steady["population"]["observed_call_count"] == 63 * projected["body_forward_span_ms"]["count"]
    assert steady["excluded_layers"][0]["observed_ms"] == projected["per_layer_ms"][0]["stats"]
    from statistics import median
    for group in steady["attention_groups"]:
        assert group["layer_count"] == {"gdn": 47, "gqa": 16}[group["attention_kind"]]
        values = [layer["observed_ms"]["p50"] for layer in layers["layers"]
                  if layer["layer_id"] != 0 and layer["attention_kind"] == group["attention_kind"]]
        assert group["comparison"]["observed_ms"] == median(values)
    sidecar = json.loads((directory / "steady-layer-pooled.json").read_text())
    actual = next(row for row in sidecar["cases"] if row["case_id"] == declaration["case_id"])
    pooled = replay.compare_pooled_layers(steady, actual)
    for group, measured in zip(pooled["groups"], actual["groups"]):
        durations = [duration for duration, count in measured["duration_ns_counter"] for _ in range(count)]
        assert group["observed_ms"]["p50"] == median(durations) / 1e6
        assert group["observed_call_count"] == len(durations)
        assert group["relative_error_vs_p50"] == pytest.approx(
            group["predicted_ms"]["p50"] / (median(durations) / 1e6) - 1)
    assert pooled["groups"][0]["observed_ms"]["p50"] != steady["population"]["comparison"]["observed_ms"]
