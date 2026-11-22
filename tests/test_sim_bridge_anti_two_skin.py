"""Regression tests for anti-'two-skin' sim-profiler bridge fixes (#478 Items 15, 16b, 17).

[Role]
  Verify canonical `(sku, topology_preset)` preservation, `kv_cache_dtype` and
  `draft_max_model_len` runtime overrides across raw captures and complete
  explicit Cases, canonical execution geometry (`phase`, `context`,
  `media_tokens_per_sequence`) at structure ingress, and `predict_cell`
  separation of `tpot_ms` (`ms/token`) vs `step_ms` (`ms/step`).
[Invariants]
  * Pure CPU Tier-0/Tier-1 tests; zero NPU contexts or host pollution.
  * Every temporary file lives inside pytest `tmp_path`.
[Timeouts & Locks]
  Deterministic in-memory and bounded `tmp_path` tests (< 10s).
[Side-Effect Policy]
  Writes only inside pytest `tmp_path`.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mindie_profiler import sim_bridge
from mindie_profiler import sim_bridge_cells as cells
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.sim_bridge_catalog import _resolve_hw_spec
from mindie_profiler.sim_structure_ingress import (
    _export_structure,
    _graph_declared,
    apply_structure_ingress,
    resolve_case_geometry,
)


def _complete_raw_capture(hardware: str = "a3-8p", *, tp: int = 8, dp: int = 2) -> dict:
    return {
        "hardware": hardware,
        "model_name": "custom-inline",
        "model_config": {
            "hidden_size": 1024,
            "num_attention_heads": 16,
            "num_hidden_layers": 2,
            "intermediate_size": 3072,
            "vocab_size": 1024,
        },
        "parallelism": {"tp": tp, "dp": dp, "ep": 1, "pp": 1},
        "workload": {
            "batch_size": 2, "seq_len": 128, "decode_steps": 8,
            "phase": "decode",
        },
        "runtime": {
            "max_num_seqs": 4,
            "max_num_batched_tokens": 512,
            "max_model_len": 4096,
            "kv_block_size": 128,
            "enable_chunked_prefill": False,
        },
    }


def test_item15_capture_reconstruction_preserves_hardware_topology_preset():
    pytest.importorskip("mindie_sim.compose")

    assert _resolve_hw_spec("a3-8p", strict=True) == ("Ascend910_9392", "a3_8p")
    assert _resolve_hw_spec("950dt-144g-pod", strict=True) == ("Ascend950DT_9581", "a5_pod")
    assert _resolve_hw_spec("capture_a3-8p_tp8_dp2", strict=False) == ("Ascend910_9392", "a3_8p")

    case_8p = sim_bridge.export_sim_case(_complete_raw_capture("a3-8p", tp=8, dp=2))
    assert case_8p["machine"]["sku"] == "Ascend910_9392"
    assert case_8p["machine"]["topology_preset"] == "a3_8p"
    assert case_8p["machine"]["ranks_per_node"] == 8

    case_bare = sim_bridge.export_sim_case(_complete_raw_capture("a3", tp=8, dp=2))
    assert case_bare["machine"]["sku"] == "Ascend910_9392"
    assert case_bare["machine"]["ranks_per_node"] == 16

    rebuilt = sim_bridge.export_sim_case(case_8p, seq_len=256)
    assert rebuilt["machine"]["topology_preset"] == "a3_8p"
    assert rebuilt["machine"]["ranks_per_node"] == 8


def test_item15_explicit_case_applies_kv_cache_dtype_and_draft_max_model_len(tmp_path: Path):
    compose_case = pytest.importorskip("mindie_sim.compose").compose_case
    from mindie_sim.prediction.capacity import Memory
    from mindie_sim.prediction.structure import parse_case

    explicit = compose_case(
        "deepseek-v3.2", "a3-8p",
        tp=8, dp=1, ep=8, layers=4,
        prompt_tokens=4096, output_tokens=64, concurrency=1,
        mtp_proposal_tokens=3, mtp_acceptance_length=2.5,
        max_model_len=8192,
    )
    assert explicit["machine"]["topology_preset"] == "a3_8p"

    # Unmodified explicit Case still roundtrips identically.
    assert sim_bridge.export_sim_case(deepcopy(explicit)) == explicit

    # Applying ONLY kv_cache_dtype + draft_max_model_len must NOT hit the unmodified early return.
    overridden = sim_bridge.export_sim_case(
        deepcopy(explicit),
        runtime_overrides={"kv_cache_dtype": "int8", "draft_max_model_len": 2048},
    )
    assert overridden["model"]["quant"]["kv_dtype"] == "int8"
    assert overridden["runtime"]["metadata"]["draft_max_model_len"] == 2048
    assert overridden["machine"]["topology_preset"] == "a3_8p"

    mem_orig = Memory(parse_case(explicit))
    mem_new = Memory(parse_case(overridden))
    assert mem_new.case.model.quant.kv_dtype == "int8"
    bd_orig = mem_orig.cache_pool_breakdown(4096, padded=True)
    bd_new = mem_new.cache_pool_breakdown(4096, padded=True)
    assert bd_new["draft_context_cap"] == 2048
    assert bd_new["draft_kv_bytes"] < bd_orig["draft_kv_bytes"]

    # Raw capture + CLI flags also honor both overrides.
    raw_out = sim_bridge.export_sim_case(
        _complete_raw_capture("a3-8p", tp=8, dp=1),
        runtime_overrides={"kv_cache_dtype": "int8", "draft_max_model_len": 2048},
    )
    assert raw_out["model"]["quant"]["kv_dtype"] == "int8"
    assert raw_out["runtime"]["metadata"]["draft_max_model_len"] == 2048

    in_path = tmp_path / "explicit.json"
    out_path = tmp_path / "overridden.json"
    in_path.write_text(json.dumps(explicit), encoding="utf-8")
    rc = sim_bridge.main([
        "export-sim-case", "--input", str(in_path),
        "--kv-cache-dtype", "int8", "--draft-max-model-len", "2048",
        "--output", str(out_path),
    ])
    assert rc == 0
    cli_case = json.loads(out_path.read_text(encoding="utf-8"))
    assert cli_case["model"]["quant"]["kv_dtype"] == "int8"
    assert cli_case["runtime"]["metadata"]["draft_max_model_len"] == 2048

    with pytest.raises(ProfilerUsageError, match="invalid_draft_max_model_len"):
        sim_bridge.export_sim_case(deepcopy(explicit), runtime_overrides={"draft_max_model_len": 0})
    with pytest.raises(ProfilerUsageError, match="invalid_draft_max_model_len"):
        sim_bridge.export_sim_case(deepcopy(explicit), runtime_overrides={"draft_max_model_len": True})


def test_item16b_structure_ingress_reads_canonical_geometry_and_forwards_media_tokens(monkeypatch):
    compose_case = pytest.importorskip("mindie_sim.compose").compose_case
    case = compose_case(
        "deepseek-v3.2", "a3", tp=8, prompt_tokens=64, output_tokens=4, layers=2,
    )

    graph_top = {
        "schema": "mindie-sim.graph/1",
        "phase": "prefill",
        "context": 0,
        "tokens_per_sequence": 512,
        "sequences_per_replica": 2,
        "media_tokens_per_sequence": 256,
        "graph_scope": "model",
        "duration_ms": 1.5,
    }
    declared_top = _graph_declared(graph_top)
    assert declared_top["phase"] == "prefill"
    assert declared_top["context"] == 0
    assert declared_top["media_tokens_per_sequence"] == 256

    _parsed, geom = resolve_case_geometry(case, declared=declared_top)
    assert geom["phase"] == "prefill"
    assert geom["context"] == 0
    assert geom["tokens"] == 512
    assert geom["sequences"] == 2
    assert geom["media_tokens_per_sequence"] == 256

    graph_nested = {
        "schema": "mindie-sim.graph/1",
        "execution": {
            "phase": "prefill",
            "tokens": 256,
            "sequences": 1,
            "context": 128,
            "scope": "body",
            "media_tokens_per_sequence": 64,
        },
        "duration_ms": 1.2,
    }
    _parsed2, geom2 = resolve_case_geometry(case, declared=_graph_declared(graph_nested))
    assert geom2 == {
        "phase": "prefill",
        "tokens": 256,
        "sequences": 1,
        "context": 128,
        "scope": "body",
        "draft_prepare": False,
        "media_tokens_per_sequence": 64,
    }

    with pytest.raises(ProfilerUsageError, match="media-tokens-per-sequence"):
        resolve_case_geometry(case, phase="prefill", tokens=64, sequences=1, context=0, media_tokens_per_sequence=-1)

    from mindie_profiler.structure_mapping import _seal_digest

    seen_calls: list[dict] = []

    def _fake_export(case_doc, **kwargs):
        seen_calls.append(dict(kwargs))
        doc = {
            "schema_version": "mindie-model-structure/1",
            "nodes": [{"node_id": "n0", "replica": "0", "stage": "0", "phase": kwargs["phase"], "layer": 0}],
            "subgraphs": [],
            "execution": {
                "phase": kwargs["phase"],
                "tokens": kwargs["tokens"],
                "context": kwargs["context"],
                "sequences": kwargs["sequences"],
                "scope": kwargs["scope"],
                "media_tokens_per_sequence": kwargs.get("media_tokens_per_sequence"),
            },
        }
        doc["graph_id"] = _seal_digest(doc)
        return doc

    import mindie_sim.structure as structure_mod

    monkeypatch.setattr(structure_mod, "export_structure", _fake_export)
    _export_structure(case, geom)
    assert seen_calls[-1]["media_tokens_per_sequence"] == 256

    # Full apply_structure_ingress regenerates directly from graph_top without repeating --phase/--context.
    monkeypatch.setattr(
        "mindie_profiler.sim_structure_ingress._compare_cohorts",
        lambda *_a, **_kw: {"status": "stubbed"},
    )
    report: dict = {}
    apply_structure_ingress(report, [], structure=graph_top, sim_case=case)
    assert seen_calls[-1]["media_tokens_per_sequence"] == 256
    assert report["structure_ingress"]["generated_structure"] is True
    assert report["structure_ingress"]["geometry"]["phase"] == "prefill"
    assert report["structure_ingress"]["geometry"]["context"] == 0
    assert report["structure_ingress"]["geometry"]["media_tokens_per_sequence"] == 256

    # Older mindie-sim lacking media_tokens_per_sequence fails honestly instead of silently dropping it.
    def _legacy_export(case_doc, *, phase, tokens, context=0, sequences=1, scope="model", source=None):
        return {"ok": True}

    monkeypatch.setattr(structure_mod, "export_structure", _legacy_export)
    with pytest.raises(ProfilerUsageError, match="media_tokens_per_sequence"):
        _export_structure(case, geom)


def test_item17_predict_cell_separates_tpot_ms_from_decode_step_ms(monkeypatch, tmp_path: Path):
    import mindie_sim

    case_path = tmp_path / "case.json"
    case_path.write_text("{}", encoding="utf-8")
    spec = cells.CellSpec(cell_id="spec4", phase="decode", model_case=case_path, prompt_tokens=64, max_tokens=5)

    monkeypatch.setattr(cells, "raw_case_for_cell", lambda _s: {})
    monkeypatch.setattr(
        "mindie_sim.prediction.structure.parse_case",
        lambda _raw: SimpleNamespace(model=SimpleNamespace(layers=2)),
    )

    # Case 1: Speculative decode committing 4 tokens in one 8.0 ms decode step -> tpot_ms=2.0, step_ms=8.0.
    def _predict_with_observer(_case, *, scope="serving", trace_limit=0, event_limit=8, observer=None):
        assert scope == "serving"
        if observer is not None:
            observer(SimpleNamespace(mode="prefill", start_ms=0.0, completion=SimpleNamespace(time=20.0)))
            observer(SimpleNamespace(mode="decode", start_ms=20.0, completion=SimpleNamespace(time=28.0)))
        return {
            "status": "modeled",
            "metrics": {
                "e2e_ms": {"p50": 28.0},
                "ttft_ms": {"p50": 20.0},
                "tpot_ms": {"p50": 2.0},
            },
            "execution": {
                "step_summary": {
                    "groups": [
                        {"mode": "prefill", "steps": 1, "duration_ms": {"sum": 20.0, "mean": 20.0}},
                        {"mode": "decode", "steps": 1, "duration_ms": {"sum": 8.0, "mean": 8.0}},
                    ]
                }
            },
        }

    monkeypatch.setattr(mindie_sim, "predict", _predict_with_observer)
    out = cells.predict_cell(spec)
    assert out["formal_point"] is True
    assert out["tpot_ms"] == pytest.approx(2.0)
    assert out["step_ms"] == pytest.approx(8.0)

    # Case 2: Mock predict without observer still reads execution.step_summary decode duration (never tpot_ms).
    def _predict_step_summary_only(_case, *, scope="serving", trace_limit=0, event_limit=8):
        return {
            "status": "modeled",
            "metrics": {"e2e_ms": {"p50": 28.0}, "ttft_ms": {"p50": 20.0}, "tpot_ms": {"p50": 2.0}},
            "execution": {
                "step_summary": {
                    "groups": [
                        {"mode": "decode", "steps": 2, "duration_ms": {"sum": 16.0, "mean": 8.0}},
                    ]
                }
            },
        }

    monkeypatch.setattr(mindie_sim, "predict", _predict_step_summary_only)
    out2 = cells.predict_cell(spec)
    assert out2["tpot_ms"] == pytest.approx(2.0)
    assert out2["step_ms"] == pytest.approx(8.0)

    # Case 3: Missing decode iteration timing leaves step_ms=None rather than copying tpot_ms.
    def _predict_no_steps(_case, *, scope="serving", trace_limit=0, event_limit=8, observer=None):
        return {
            "status": "modeled",
            "metrics": {"e2e_ms": {"p50": 28.0}, "ttft_ms": {"p50": 20.0}, "tpot_ms": {"p50": 2.0}},
            "execution": {"step_summary": {"groups": []}},
        }

    monkeypatch.setattr(mindie_sim, "predict", _predict_no_steps)
    out3 = cells.predict_cell(spec)
    assert out3["tpot_ms"] == pytest.approx(2.0)
    assert out3["step_ms"] is None


def test_item17_predict_cell_live_speculative_decode_step_ms_exceeds_tpot_ms(tmp_path: Path):
    compose_case = pytest.importorskip("mindie_sim.compose").compose_case

    spec_case = compose_case(
        "qwen3-32b", "a3",
        tp=1, dp=1, ep=1, layers=2,
        prompt_tokens=64, output_tokens=9, concurrency=1,
        mtp_proposal_tokens=3, mtp_acceptance_length=4.0,
        allow_synthetic_gqa_draft=True,
    )
    case_path = tmp_path / "spec_decode.json"
    case_path.write_text(json.dumps(spec_case), encoding="utf-8")

    result = cells.predict_cell(cells.CellSpec(
        cell_id="live-spec4", phase="decode", model_case=case_path,
        prompt_tokens=64, max_tokens=9, concurrency=1, tp=1, dp=1, ep=1, pp=1,
    ))
    assert result["formal_point"] is True, result
    assert result["tpot_ms"] is not None and result["tpot_ms"] > 0.0
    assert result["step_ms"] is not None and result["step_ms"] > 0.0
    # Committing 4 tokens per speculative decode step makes step_ms ~= 4 * tpot_ms (never == tpot_ms).
    assert result["step_ms"] / result["tpot_ms"] == pytest.approx(4.0, rel=0.15)
