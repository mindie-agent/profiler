"""Body comparison reuses the causal Sim API and keeps placement boundaries."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def adapter():
    pytest.importorskip("mindie_sim.prediction.body")
    path = Path(__file__).resolve().parents[1] / "examples/structure/body_forward_comparison.py"
    spec = importlib.util.spec_from_file_location("body_forward_comparison", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def case():
    sim = pytest.importorskip("mindie_sim")
    path = Path(sim.__file__).resolve().parents[1] / "examples/quickstart.json"
    if not path.exists():
        pytest.skip("Sim source example is required for this cross-repository contract test")
    return json.loads(path.read_text())


def test_body_uses_complete_semantic_timeline_with_zero_engine_trace(adapter, case):
    from mindie_sim import predict

    result = predict(case, scope="body", tokens=2, context=64, sequences=2, event_limit=0)
    projected = adapter.summarize_prediction(case, result)
    assert result["events"] == []
    assert projected["timeline_complete"]
    assert projected["body_forward_span_ms"] == result["duration_ms"]
    assert projected["first_kernel_ready_ms"] == 0
    assert projected["first_kernel_to_body_complete_ms"] == result["duration_ms"]
    assert len(projected["per_layer_ms"]) == case["model"]["layers"]
    for layer in projected["per_layer_ms"]:
        rows = [r for r in result["timeline"] if r["layer"] == layer["layer_id"]]
        assert layer["span_ms"] == pytest.approx(
            max(r["complete_ms"] for r in rows) - min(r["ready_ms"] for r in rows))
    # Missing semantic rows must not silently produce a complete layer report.
    partial = deepcopy(result)
    partial["timeline"] = [r for r in partial["timeline"] if r["layer"] != 2]
    assert adapter.summarize_prediction(case, partial)["status"] == "partial"


def test_ep_replicas_keep_envelopes_without_adding_parallel_layer_spans(adapter, case):
    raw = deepcopy(case)
    raw["machine"]["num_devices"] = 2
    raw["machine"]["links"] = [{"name": "fabric", "capacity_bytes_per_ms": 1e8,
                                  "members": [0, 1], "semantics": "shared"}]
    raw["model"].update(ffn="moe", num_experts=4, top_k=2, moe_intermediate_size=512)
    raw["runtime"].update(dp=2, ep=2, tp=1, graph_mode="none")
    result = adapter.predict_body(raw, tokens=1, context=64, sequences=2)
    assert result["geometry"]["participating_replicas"] == [0, 1]
    assert len(result["per_layer_ms"]) == 2 * raw["model"]["layers"]
    assert {r["kind"] for r in result["per_layer_ms"]} == {"moe_layer"}
    assert {r["attention_kind"] for r in result["per_layer_ms"]} == {"gqa"}
    assert sum(r["span_ms"] for r in result["replica_envelopes_ms"]) > result["body_forward_span_ms"]
    assert result["body_forward_span_ms"] == pytest.approx(
        max(r["span_ms"] for r in result["replica_envelopes_ms"]))


def test_forward_comparison_requires_equal_phase_query_context_and_placement(adapter, case):
    result = adapter.predict_body(case, tokens=4, context=1024, sequences=2)
    observed = {
        "status": "measured", "metric_boundary": result["metric_boundary"],
        "span_start_basis": "first_retained_device_event_start",
        "span_end_basis": "last_retained_device_event_end",
        "geometry": deepcopy(result["geometry"]),
        "body_forward_span_ms": {"count": 3, "mean": result["body_forward_span_ms"] / 1.1,
                                 "p50": None, "p90": None},
    }
    observed["comparison_scope"] = {
        "kind": "complete_target_body_cohort", "boundary_relation": {
            "predicted_start_basis": result["span_start_basis"],
            "predicted_end_basis": result["span_end_basis"],
            "observed_start_basis": observed["span_start_basis"],
            "observed_end_basis": observed["span_end_basis"],
            "relation": "equivalent_start_and_end",
            "evidence": {"reference": "test-only declared equality for comparison arithmetic"},
        },
    }
    compared = adapter.compare_body_forward(result, observed)
    assert compared["relative_error"] == pytest.approx(.1)
    assert compared["passed"] is True
    observed["geometry"]["tokens_per_sequence"] = 1
    observed["geometry"].pop("participating_replicas")
    unresolved = adapter.compare_body_forward(result, observed)
    assert unresolved["status"] == "unresolved"
    assert unresolved["passed"] is None
    assert unresolved["reasons"] == ["geometry_differs:tokens_per_sequence",
                                     "observed_geometry_missing:participating_replicas"]


def test_unresolved_forward_never_becomes_scored_by_a_numerical_span(adapter, case):
    predicted = adapter.predict_body(case, tokens=1, context=64)
    observed = {"status": "unresolved", "metric_boundary": "step_envelope",
                "geometry": predicted["geometry"],
                "body_forward_span_ms": {"count": 1, "mean": predicted["body_forward_span_ms"]}}
    result = adapter.compare_body_forward(predicted, observed)
    assert result["status"] == "unresolved"
    assert result["relative_error"] is None
    assert "forward_metric_boundary_differs" in result["reasons"]
    assert result["endpoints"]["kernel_startup_included"] is True


def test_layer_error_uses_declared_ordinal_and_ffn_kind_without_replica_sum(adapter, case):
    predicted = adapter.predict_body(case, tokens=2, context=64)
    observed = {"per_layer_ms": [{
        "layer_id": row["layer_id"], "kind": row["kind"], "rank_id": "rank_0",
        "stats": {"count": 3, "mean": row["span_ms"] / 1.25,
                  "p50": row["span_ms"] / 1.25, "p90": row["span_ms"] / 1.25},
    } for row in predicted["per_layer_ms"]]}
    result = adapter.compare_layers(predicted, observed)
    assert result["summary"]["compared_layers"] == case["model"]["layers"]
    assert result["summary"]["passed_layers"] == 0
    assert all(row["relative_error"] == pytest.approx(.25) for row in result["layers"])
    assert result["ffn_kind_distributions"][0]["observed_ms"]["count"] == case["model"]["layers"]
