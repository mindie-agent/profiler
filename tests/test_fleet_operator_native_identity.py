"""Declared native identity and accelerator-core publication.

[Role]
  Recover native kinds the compact record already carries, and publish an
  accelerator class only from a declared MSProf field.

[Invariants]
  * A family name, program name, or resource-busy label is not a core.
  * Unbound cores stay None. They are not filled with zero and are not a
    share of the step scalar.
  * Modeled kernel elapsed is not divided by a registered forward-window count.
  * Deleting or rotating measured regime fields does not change the forecast.

[Timeouts & Locks]
  In-memory. One registered GLM body.

[Side-Effect Policy]
  Reads the registered case. Writes nothing.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

_PROFILER_ROOT = Path(os.environ.get("MINDIE_PROFILER_ROOT", "/Users/maoxx241/code/profiler"))
ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "examples" / "structure").is_dir() and (_PROFILER_ROOT / "examples" / "structure").is_dir():
    ROOT = _PROFILER_ROOT
STRUCT_DIR = ROOT / "examples" / "structure"
if str(STRUCT_DIR) not in sys.path:
    sys.path.insert(0, str(STRUCT_DIR))

import fleet_operator_modeling as fom  # noqa: E402


def _glm_cfg() -> dict:
    return {
        "capture_id": "registered_decode:glm53flash-a3-tp16-c4-livepre",
        "suite": "registered_decode",
        "hardware_tier": "A3",
        "phase": "decode",
        "model_case": "cases/decode-glm53flash-a3-tp16-c4-livepre.json",
        "forward_steps": 73,
        "geometry": {
            "tp": 16, "dp": 1, "ep": 16,
            "sequences_per_replica": 4, "tokens_per_sequence": 6, "query_rows": 24,
            "context_tokens": 4096, "context_basis": "not_observed_from_cache_capacity",
        },
    }


def _replica(family: str, elapsed: float, **extra) -> dict:
    record = {
        "family": family,
        "phase": "decode",
        "operator_events": 1,
        "elapsed_ms": elapsed,
    }
    record.update(extra)
    return record


def test_source_disjoint_labels_do_not_invent_a_core_and_a_declared_class_is_counted_once() -> None:
    """Names and resource labels stay unbound. A declared class is one duration."""
    profile = {
        "by_operator": {
            "s0:hc": {
                "op_id": "hc_pre.native",
                "elapsed_ms": 1.5,
                "operator_events": 1,
                "replicas": {
                    0: _replica(
                        "native_fusion", 1.5,
                        recipe="declared_native_fusion", program="OperatorPlan",
                        fusion_role="hc_pre",
                        native_implementation={"native_kind": "HcPre", "accelerator_core": "MIX_AIC"},
                    ),
                },
            },
            "s0:pair": {
                "op_id": "grouped.native",
                "elapsed_ms": 0.8,
                "operator_events": 1,
                "replicas": {
                    0: _replica(
                        "native_fusion", 0.8,
                        recipe="declared_native_fusion", program="OperatorPlan",
                        native_implementation={"native_kinds": ["GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2"]},
                    ),
                },
            },
            "s0:down": {
                "op_id": "dense_down",
                "elapsed_ms": 2.0,
                "operator_events": 1,
                "replicas": {
                    0: _replica("gemm", 2.0, program="SteadyMatmul", recipe="dense_down", engine="vector@r0:s0"),
                },
            },
            "s0:reduce": {
                "op_id": "allreduce",
                "elapsed_ms": 0.4,
                "operator_events": 1,
                "replicas": {0: _replica("allreduce", 0.4, program="RingCollective")},
            },
            "s0:cpu": {
                "op_id": "cpu_tail",
                "elapsed_ms": 0.25,
                "operator_events": 1,
                "replicas": {0: _replica("elementwise", 0.25, accelerator_core="AI_CPU")},
            },
            "s0:split": {
                "op_id": "mixed",
                "elapsed_ms": 0.3,
                "operator_events": 1,
                "replicas": {
                    0: _replica(
                        "native_fusion", 0.3,
                        native_implementation={"native_kinds": ["HcPre", "AllReduce"]},
                    ),
                },
            },
        },
        "by_family": {
            "native_fusion": {"elapsed_ms": 2.6},
            "gemm": {"elapsed_ms": 2.0},
            "allreduce": {"elapsed_ms": 0.4},
            "elementwise": {"elapsed_ms": 0.25},
        },
    }
    bucket, elapsed, _counted = fom._classify_compact_profile(profile)
    # The disagreeing HcPre/AllReduce replica blocks a native_fusion lump move.
    # The family name "elementwise" is not an elementwise_quant token, so it stays other.
    assert bucket["canonical"]["other"] == pytest.approx(2.85)
    assert bucket["canonical"]["gemm"] == pytest.approx(2.0)
    assert bucket["canonical"]["collective"] == pytest.approx(0.4)
    assert elapsed == pytest.approx(5.25)

    uniform = {
        "by_operator": {
            "s0:hc": profile["by_operator"]["s0:hc"],
            "s0:pair": profile["by_operator"]["s0:pair"],
            "s0:down": profile["by_operator"]["s0:down"],
        },
        "by_family": {
            "native_fusion": {"elapsed_ms": 2.3},
            "gemm": {"elapsed_ms": 2.0},
        },
    }
    moved, moved_elapsed, _moved_count = fom._classify_compact_profile(uniform)
    assert moved_elapsed == pytest.approx(4.3)
    assert moved["canonical"]["moe"] == pytest.approx(2.3)
    assert moved["canonical"]["gemm"] == pytest.approx(2.0)
    assert moved["canonical"]["other"] == pytest.approx(0.0)

    ledger = fom._program_ledger(profile)
    by_frame = {row["frame_id"]: row for row in ledger}
    assert by_frame["s0:hc"]["native_op"] == "HcPre"
    assert by_frame["s0:hc"]["engine"] == "MIX_AIC"
    assert by_frame["s0:hc"]["declared_engine"] == "MIX_AIC"
    assert by_frame["s0:hc"]["family_scope"] == "moe"
    assert by_frame["s0:hc"]["program"] == "OperatorPlan"
    assert by_frame["s0:pair"]["native_op"] is None
    assert by_frame["s0:pair"]["native_kinds"] == ["GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2"]
    assert by_frame["s0:pair"]["native_selection"] == "unselected_variants"
    assert by_frame["s0:pair"]["family_scope"] == "moe"
    assert by_frame["s0:pair"]["engine"] is None
    assert by_frame["s0:down"]["declared_engine"] == "vector@r0:s0"
    assert by_frame["s0:down"]["engine"] is None
    assert by_frame["s0:down"]["native_op"] is None
    assert by_frame["s0:reduce"]["engine"] is None
    assert by_frame["s0:cpu"]["declared_engine"] == "AI_CPU"
    assert by_frame["s0:cpu"]["engine"] == "AI_VECTOR_CORE"
    assert by_frame["s0:split"]["family_identity"] == "partial_kinds"
    assert by_frame["s0:split"]["native_kinds"] == ["HcPre", "AllReduce"]
    assert by_frame["s0:split"]["family_scope"] is None

    published = fom._core_publication(ledger, elapsed)
    assert published["core_forecast"] == "partial"
    assert published["core_map_is_complete_forecast"] is False
    assert published["predicted_by_core_ms"]["MIX_AIC"] == pytest.approx(1.5)
    assert published["predicted_by_core_ms"]["AI_VECTOR_CORE"] == pytest.approx(0.25)
    assert published["predicted_by_core_ms"]["AI_CORE"] is None
    assert published["predicted_by_core_ms"]["COMMUNICATION"] is None
    assert published["predicted_by_core_ms"]["AI_CPU"] is None
    assert published["predicted_by_core_ms"]["MIX_AIV"] is None
    assert 0 not in published["predicted_by_core_ms"].values()
    assert published["bound_core_elapsed_ms"] == pytest.approx(1.75)
    assert published["unresolved_core_elapsed_ms"] == pytest.approx(elapsed - 1.75)

    aiv = fom._program_ledger({
        "by_operator": {
            "s0:aiv": {
                "op_id": "aiv",
                "replicas": {0: _replica("elementwise", 0.7, accelerator_core="MIX_AIV")},
            },
        },
    })
    aiv_pub = fom._core_publication(aiv, 0.7)
    assert aiv[0]["declared_engine"] == "MIX_AIV"
    assert aiv_pub["predicted_by_core_ms"]["COMMUNICATION"] == pytest.approx(0.7)
    assert aiv_pub["predicted_by_core_ms"]["AI_VECTOR_CORE"] is None
    assert aiv_pub["predicted_by_core_ms"]["MIX_AIV"] is None
    assert aiv_pub["core_forecast"] == "source_bound"

    busy = fom._core_publication([
        {"native_op": "Matmul", "engine": None, "declared_engine": "matrix@r0", "elapsed_ms": 4.0, "unit": "ms", "rank_id": 0},
    ], 4.0)
    assert busy["core_forecast"] == "unresolved"
    assert all(value is None for value in busy["predicted_by_core_ms"].values())
    assert busy["unresolved_core_elapsed_ms"] == pytest.approx(4.0)
    assert busy["bound_core_elapsed_ms"] == 0.0

    foreign = fom._program_ledger({
        "by_operator": {
            "s0:us": {
                "op_id": "us",
                "replicas": {0: _replica("gemm", 3.0, accelerator_core="AI_CORE", unit="us")},
            },
        },
    })
    foreign_pub = fom._core_publication(foreign, 3.0)
    assert foreign[0]["unit"] == "us"
    assert foreign_pub["core_forecast"] == "unresolved"
    assert foreign_pub["predicted_by_core_ms"]["AI_CORE"] is None

    multi = fom._core_publication([
        {"engine": "AI_CORE", "elapsed_ms": 1.0, "unit": "ms", "rank_id": 0},
        {"engine": "AI_CORE", "elapsed_ms": 1.0, "unit": "ms", "rank_id": 1},
    ], 2.0)
    assert multi["core_forecast"] == "withheld_multi_rank"
    assert all(value is None for value in multi["predicted_by_core_ms"].values())
    assert multi["unresolved_core_elapsed_ms"] == pytest.approx(2.0)


def test_registered_glm_recovers_fusion_kinds_and_leaves_cores_unresolved() -> None:
    """The registered GLM body keeps its span. Fusion kinds move. Cores stay unbound."""
    fom.clear_caches()
    cfg = _glm_cfg()
    base = fom.predict_capture_operators_and_step(cfg)
    assert base["status"] == "modeled"
    assert base["measurement_features_read"] is False
    assert base["predicted_step_ms"] == base["predicted_operator_ms"]
    assert base["predicted_step_ms"] != pytest.approx(29.76155106521739)
    coverage = base["coverage"]
    assert coverage["core_forecast"] == "unresolved"
    assert coverage["core_map_is_complete_forecast"] is False
    assert coverage["bound_core_elapsed_ms"] == 0.0
    assert coverage["unresolved_core_elapsed_ms"] == base["predicted_operator_ms"]
    assert coverage["partial_kind_elapsed_ms"] == 0.0
    assert all(value is None for value in base["predicted_by_core_ms"].values())
    assert 0 not in base["predicted_by_core_ms"].values()
    assert "MIX_AIC" in coverage["cores_unnamed_by_engine"]
    assert coverage["resource_busy_is_not_accelerator_core_elapsed"] is True
    resources = {row["resource"] for row in base["resources"]}
    assert any(str(name).startswith("vector@") for name in resources)
    assert any(str(name).startswith("matrix@") for name in resources)

    recovered = coverage["recovered_native_kind_ms"]
    pair = "GroupedMatmulSwigluQuant+GroupedMatmulSwigluQuantV2"
    assert set(recovered) == {"HcPre", "HcPost", pair}
    assert sum(recovered.values()) == pytest.approx(base["predicted_by_canonical_family_ms"]["moe"])
    assert recovered["HcPre"] > 0.0 and recovered["HcPost"] > 0.0 and recovered[pair] > 0.0
    unresolved = coverage["unresolved_family_identity_ms"]
    assert "RecurrentKda" in unresolved
    assert unresolved["RecurrentKda"] > 0.0
    assert "router" in unresolved
    assert sum(unresolved.values()) == pytest.approx(base["predicted_by_canonical_family_ms"]["other"])

    rows = base["additive_rank_phase"]["rows"]
    hc = next(row for row in rows if row.get("native_op") == "HcPre")
    assert hc["program"] == "OperatorPlan"
    assert hc["recipe"] == "declared_native_fusion"
    assert hc["phase"] == "decode"
    assert hc["rank_id"] == 0
    assert hc["engine"] is None
    assert hc["family_scope"] == "moe"
    assert hc["frame_id"]
    recurrent = next(row for row in rows if row.get("native_op") == "RecurrentKda")
    assert recurrent["family_identity"] == "declared_kind_unscoped"
    assert recurrent["family_scope"] == "other"
    assert recurrent["engine"] is None
    down = next(row for row in rows if row.get("recipe") == "dense_down")
    assert down["native_op"] is None
    assert down["engine"] is None

    original = fom._load_case

    def rotated(path, expected):
        document, error = original(path, expected)
        if not isinstance(document, dict):
            return document, error
        kernels = document["runtime"]["kernels"]
        for regime in list(kernels.get("service_regimes") or []):
            response = regime.get("response") if isinstance(regime.get("response"), dict) else {}
            response.pop("fixed_us", None)
            response.pop("fixed_ms", None)
            response.pop("knots", None)
            execution = regime.get("execution") if isinstance(regime.get("execution"), dict) else {}
            execution.pop("resource", None)
        kernels.pop("service_regimes", None)
        rates = document["machine"]["device"].get("rates")
        if isinstance(rates, dict):
            rates.pop("observed_a3_local_native", None)
            rates["rotated_observed_rate"] = 1.0e12
        return document, error

    fom._load_case = rotated
    try:
        fom.clear_caches()
        mutated = fom.predict_capture_operators_and_step(cfg)
    finally:
        fom._load_case = original
    assert mutated["predicted_step_ms"] == base["predicted_step_ms"]
    assert mutated["predicted_by_canonical_family_ms"] == base["predicted_by_canonical_family_ms"]
    assert mutated["predicted_by_family_ms"] == base["predicted_by_family_ms"]
    assert mutated["predicted_by_core_ms"] == base["predicted_by_core_ms"]
    assert mutated["coverage"]["unresolved_core_elapsed_ms"] == coverage["unresolved_core_elapsed_ms"]
    assert mutated["coverage"]["recovered_native_kind_ms"] == recovered
    assert mutated["coverage"]["core_forecast"] == "unresolved"
