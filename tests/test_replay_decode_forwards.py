"""Missing evidence and source mismatches never turn into numerical accuracy."""
import importlib.util
from copy import deepcopy
import json
from pathlib import Path

import pytest
from tests.sim_fixtures import case_path

from mindie_profiler.sources_db import sha256_file


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def replay(monkeypatch):
    directory = ROOT / "examples/structure"
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location("decode_forward_replay", directory / "decode.py")
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
    assert "target_body_boundary_evidence_missing" in row["comparison"]["reasons"]


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
    observed = json.loads((ROOT / 'tests/fixtures/pipeline/mixed_decode_populations.json').read_text())
    declaration = {"case_id": "v4flash-a3-tp8-c4", "geometry": {"context_tokens": 4096}}
    scenarios = replay._automatic_scenarios(declaration, observed)
    result = {"case_id": declaration["case_id"]}
    replay._compare_scenarios(result, scenarios, None, {}, prediction_timeout_s=1,
                             run_predictions=False, geometry_limit=1)
    rows = result["geometry_cases"]
    assert [row["comparison"]["observed_forward_count"] for row in rows] == [104, 4]
    assert rows[0]["comparison"]["reasons"] == ["prediction_not_requested"]
    assert rows[1]["comparison"]["reasons"] == ["prediction_deferred_by_population_priority"]
    assert sum(row["comparison"]["observed_forward_count"] for row in rows) == observed["body_forward_span_ms"]["count"]
    assert all(row["comparison"]["predicted_ms"] is None for row in rows)



@pytest.mark.parametrize("relation", [None, "in_sample", "heldout"])
def test_reused_capture_retains_explicit_calibration_without_inferring_fit(
        replay, monkeypatch, tmp_path, relation):
    sim = pytest.importorskip("mindie_sim")
    from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.events import SourceRef

    source = ROOT / "tests/fixtures/decode_forward/qwen36_a3_verify.csv"
    model_path = case_path('qwen36-a3-tp4.json')
    case = json.loads(model_path.read_text())
    config = replay._model_config(case)
    reference = SourceRef("rank_0", 0, "csv", str(source), source.name,
                          sha256_file(source), source.stat().st_size, "retained", "fixture")
    observed = auto_segment_decode_forwards(kernel_rows(source, rank_id="rank_0"), config, source=reference)
    extraction = tmp_path / "extraction.json"
    extraction.write_text(json.dumps(observed))
    identity = observed["source_identity"]
    row = {"case_id": "retained-qwen36-forward", "source": identity,
           "sim_case_path": str(model_path), "extraction_path": str(extraction),
           "geometry": {"context_tokens": 4096}}
    if relation is not None:
        row['calibration'] = {'origin': 'explicit_manifest', 'evaluation_relation': relation,
                              'evidence_refs': [identity]}
    unchanged = deepcopy((row, case, observed))

    def forbidden(*args, **kwargs):
        pytest.fail("retained metadata replay must not parse raw events or execute a model")

    monkeypatch.setattr(replay, "_source", forbidden)
    monkeypatch.setattr(replay, "_predict_bounded", forbidden)
    result = replay.replay_case(row, ROOT, run_predictions=False)
    geometries = result["geometry_cases"]
    assert sum(item["comparison"]["observed_forward_count"] for item in geometries) == 1
    for item in [result, *geometries]:
        assert item["calibration_origin"] == ("explicit_manifest" if relation else "not_declared")
        assert item["calibration_evidence"]["evaluation_relation"] == (relation or "not_declared")
        assert item["calibration_evidence"]["evidence_refs"] == ([identity] if relation else [])
    assert result["observed"]["geometry_groups"] == observed["geometry_groups"]
    assert (row, case, observed) == unchanged
    assert all(item["prediction"] is None for item in geometries)



def test_prediction_worker_has_bounded_receipt_and_reuses_completed_geometry(replay, monkeypatch, tmp_path):
    sim = pytest.importorskip("mindie_sim.prediction.body")
    path = case_path('quickstart.json')
    geometry = {"phase": "decode", "tokens_per_sequence": 1,
                "context_tokens": 16, "sequences_per_replica": 1}
    cache = {}
    first = replay._predict_bounded(path, geometry, cache, timeout_s=10)
    assert first["status"] == "completed"
    assert first["execution"]["peak_rss_bytes"] <= 512 * 1024 ** 2
    assert first["runtime_identity"]["sources_unchanged"]

    def duplicate(*args, **kwargs):
        pytest.fail("identical completed case geometry must not start another worker")

    monkeypatch.setattr(replay.subprocess, "run", duplicate)
    second = replay._predict_bounded(path, geometry,
                                     cache, timeout_s=10)
    assert second["reused_prediction"]
    assert second["prediction"] == first["prediction"]


def test_real_forward_activity_preserves_stream_union_and_layer_populations(replay):
    from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
    from mindie_profiler.normalized import kernel_rows

    fixture = ROOT / 'tests/fixtures/decode_forward'
    observed = auto_segment_decode_forwards(kernel_rows(fixture / 'qwen36_a3_verify.csv'),
        json.loads((fixture / 'model_config.json').read_text()))
    scenario, = replay._automatic_scenarios({'geometry': {'context_tokens': 4096}}, observed)
    projected = scenario['observed']
    assert projected['body_activity_ms'] == observed['body_activity_ms']
    assert projected['body_internal_gap_ms'] == observed['body_internal_gap_ms']
    assert projected['body_activity_ms']['mean'] + projected['body_internal_gap_ms']['mean'] == pytest.approx(
        projected['body_forward_span_ms']['mean'])
    forward = observed['forwards'][0]
    assert sum(row['activity_union_ms'] for row in forward['per_stream_activity_ms']) >= forward['body_activity_ms']
    assert forward['body_activity_ms'] + forward['body_internal_gap_ms'] == pytest.approx(
        (forward['end_ns'] - forward['start_ns']) / 1e6)
    assert len(projected['per_layer_ms']) == 64
    for layer in projected['per_layer_ms']:
        assert layer['activity_ms_stats']['mean'] + layer['internal_gap_ms_stats']['mean'] == pytest.approx(layer['stats']['mean'])


@pytest.mark.parametrize('valid,physical', [(6, 8), (12, 16)])
def test_real_unpadded_head_keeps_valid_requests_and_physical_graph_rows(replay, valid, physical):
    from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
    from mindie_profiler.normalized import kernel_rows

    fixture = ROOT / 'tests/fixtures/decode_forward'
    observed = auto_segment_decode_forwards(
        kernel_rows(fixture / f'kimi4_tp8_head_unpad_c{valid}.csv'),
        json.loads((fixture / 'kimi4_tp8_model_config.json').read_text()))
    declaration = {'geometry': {'context_tokens': 126000}}
    case = {'runtime': {'metadata': {'speculation': {'enabled': False}}}}
    scenario, = replay._automatic_scenarios(declaration, observed, case)
    assert scenario['geometry']['sequences_per_replica'] == valid
    assert scenario['geometry']['query_rows'] == valid
    assert scenario['geometry']['physical_query_rows'] == physical
    assert scenario['geometry']['output_query_rows'] == valid
    assert observed['geometry_groups'][0]['geometry']['query_rows'] == physical
    # Speculative logits may select only some requests: a missing or enabled
    # speculation declaration cannot turn output rows into valid batch proof.
    for model in ({}, {'runtime': {'metadata': {'speculation': {'enabled': True}}}}):
        uncertain, = replay._automatic_scenarios(declaration, observed, model)
        assert uncertain['geometry']['sequences_per_replica'] == physical
        assert 'physical_query_rows' not in uncertain['geometry']


def test_tp16_capture_padding_is_distinct_from_sequence_parallel_padding(replay):
    pytest.importorskip('mindie_sim')
    from body import predict_body, compare_body_forward
    case = json.loads((ROOT / 'examples/structure/cases/a3-kimi4-tp16-longctx-source.json').read_text())
    predicted = predict_body(case, tokens=1, sequences=6, context=4096)
    geometry = predicted['geometry']
    assert geometry['valid_query_tokens_by_replica'] == {0: 6}
    assert geometry['graph_query_tokens_by_replica'] == {0: 8}
    assert geometry['padded_query_tokens_by_replica'] == {0: 16}
    # Arithmetic control isolates the boundary comparison from model accuracy.
    observed = {'status': 'measured', 'metric_boundary': predicted['metric_boundary'],
        'basis': 'structure_guided_topology_alignment',
        'geometry': {**geometry, 'physical_query_rows': 8},
        'body_forward_span_ms': {'count': 1, 'mean': predicted['first_kernel_to_body_complete_ms']}}
    assert compare_body_forward(predicted, observed)['status'] == 'compared'
    observed['geometry']['physical_query_rows'] = 16
    assert 'geometry_differs:physical_query_rows' in compare_body_forward(predicted, observed)['reasons']
