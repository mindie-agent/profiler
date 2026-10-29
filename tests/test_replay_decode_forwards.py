"""Missing evidence and source mismatches never turn into numerical accuracy."""
import importlib.util
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
