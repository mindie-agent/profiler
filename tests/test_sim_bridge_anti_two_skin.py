"""Regression tests for standalone profiler bridge & geometry invariants.

[Role]
  Verify canonical `(sku, topology_preset)` resolution, parallel override
  parsing (`TP`/`DCP`/`PCP` env vars and CLI flags), canonical execution
  geometry (`phase`, `context`, `media_tokens_per_sequence`, `draft_prepare`)
  at structure ingress, and standalone `export_sim_case` behavior without
  requiring `mindie_sim`.
[Invariants]
  * Pure CPU Tier-0/Tier-1 tests; zero NPU contexts, zero `mindie_sim`
    runtime dependency, and zero host pollution.
  * Every temporary file lives inside pytest `tmp_path`.
[Timeouts & Locks]
  Deterministic in-memory and bounded `tmp_path` tests (< 10s).
[Side-Effect Policy]
  Writes only inside pytest `tmp_path`.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

from mindie_profiler import sim_bridge
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.sim_bridge_catalog import _parallel_overrides, _resolve_hw_spec
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


def _minimal_case() -> dict:
    return {
        "machine": {"backend": "ascend", "sku": "Ascend910_9392", "num_devices": 8},
        "model": {"name": "deepseek-v3.2", "layers": 2},
        "runtime": {"parallel": {"tp": 8, "dp": 1, "ep": 1, "pp": 1}},
    }


def _stub_compose(monkeypatch) -> list[dict]:
    calls: list[dict] = []

    def _compose_case(model, hardware, **kwargs):
        calls.append({"model": model, "hardware": hardware, **kwargs})
        preset = kwargs.get("topology_preset")
        ranks_per_node = 8 if preset == "a3_8p" else 16
        machine = {
            "backend": "ascend",
            "sku": hardware,
            "ranks_per_node": ranks_per_node,
            "num_devices": int(kwargs.get("tp", 1)) * int(kwargs.get("dp", 1)),
        }
        if preset:
            machine["topology_preset"] = preset
        quant = dict(kwargs.get("quant") or {}) if isinstance(kwargs.get("quant"), dict) else {}
        if kwargs.get("kv_cache_dtype"):
            quant["kv_dtype"] = kwargs["kv_cache_dtype"]
        runtime_meta = {}
        if kwargs.get("draft_max_model_len") is not None:
            runtime_meta["draft_max_model_len"] = kwargs["draft_max_model_len"]
        conc = max(1, int(kwargs.get("concurrency", 1)))
        prompt = int(kwargs.get("prompt_tokens", 128))
        output = int(kwargs.get("output_tokens", 8))
        return {
            "machine": machine,
            "model": {
                "name": model if isinstance(model, str) else "custom-inline",
                "quant": quant,
                "layers": 2,
                "hidden_size": 1024,
                "num_attention_heads": 16,
                "num_hidden_layers": 2,
                "intermediate_size": 3072,
                "vocab_size": 1024,
            },
            "workload": {
                "requests": [
                    {
                        "request_id": f"req-{idx}",
                        "arrival_ms": 0.0,
                        "prompt_tokens": prompt,
                        "output_tokens": output,
                        "prefix_tokens": 0,
                    }
                    for idx in range(conc)
                ],
            },
            "runtime": {
                "parallel": {
                    "tp": kwargs.get("tp", 1),
                    "dp": kwargs.get("dp", 1),
                    "ep": kwargs.get("ep", 1),
                    "pp": kwargs.get("pp", 1),
                },
                "metadata": runtime_meta,
            },
            "slo": {},
        }

    fake_pkg = ModuleType("mindie_sim")
    fake_compose = ModuleType("mindie_sim.compose")
    fake_compose.compose_case = _compose_case  # type: ignore[attr-defined]
    fake_pkg.compose = fake_compose  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mindie_sim", fake_pkg)
    monkeypatch.setitem(sys.modules, "mindie_sim.compose", fake_compose)
    return calls


def test_hardware_topology_preset_resolution_and_inline_case_export(monkeypatch):
    assert _resolve_hw_spec("a3-8p", strict=True) == ("Ascend910_9392", "a3_8p")
    assert _resolve_hw_spec("950dt-144g-pod", strict=True) == ("Ascend950DT_9581", "a5_pod")
    assert _resolve_hw_spec("capture_a3-8p_tp8_dp2", strict=False) == ("Ascend910_9392", "a3_8p")

    # Without mindie_sim installed, case composition fails honestly.
    with pytest.raises(ProfilerUsageError, match="mindie_sim is required for sim-case composition"):
        sim_bridge.export_sim_case(_complete_raw_capture("a3-8p", tp=8, dp=2))

    # With optional mindie_sim.compose present, topology_preset and chip overrides propagate cleanly.
    _stub_compose(monkeypatch)
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

    same_alias = sim_bridge.export_sim_case(deepcopy(case_8p), chip="a3")
    assert same_alias["machine"]["sku"] == "Ascend910_9392"
    assert same_alias["machine"]["topology_preset"] == "a3_8p"
    assert same_alias["machine"]["ranks_per_node"] == 8

    other_sku = sim_bridge.export_sim_case(deepcopy(case_8p), chip="a2")
    assert other_sku["machine"]["sku"] == "Ascend910B4"
    assert other_sku["machine"].get("topology_preset") != "a3_8p"

    override_preset = sim_bridge.export_sim_case(deepcopy(case_8p), chip="a3-16p")
    assert override_preset["machine"]["sku"] == "Ascend910_9392"
    assert override_preset["machine"]["topology_preset"] == "a3_16p"
    assert override_preset["machine"]["ranks_per_node"] == 16


def test_raw_capture_kv_cache_dtype_and_draft_max_model_len(monkeypatch, tmp_path: Path):
    _stub_compose(monkeypatch)
    raw_out = sim_bridge.export_sim_case(
        _complete_raw_capture("a3-8p", tp=8, dp=1),
        runtime_overrides={"kv_cache_dtype": "int8", "draft_max_model_len": 2048},
    )
    assert raw_out["model"]["quant"]["kv_dtype"] == "int8"
    assert raw_out["runtime"]["metadata"]["draft_max_model_len"] == 2048

    in_path = tmp_path / "explicit.json"
    out_path = tmp_path / "overridden.json"
    in_path.write_text(json.dumps(raw_out), encoding="utf-8")
    rc = sim_bridge.main([
        "export-sim-case", "--input", str(in_path),
        "--kv-cache-dtype", "fp8_e4m3", "--draft-max-model-len", "1024",
        "--output", str(out_path),
    ])
    assert rc == 0
    cli_case = json.loads(out_path.read_text(encoding="utf-8"))
    assert cli_case["model"]["quant"]["kv_dtype"] == "fp8_e4m3"
    assert cli_case["runtime"]["metadata"]["draft_max_model_len"] == 1024

    with pytest.raises(ProfilerUsageError, match="invalid_draft_max_model_len"):
        sim_bridge.export_sim_case(deepcopy(raw_out), runtime_overrides={"draft_max_model_len": 0})
    with pytest.raises(ProfilerUsageError, match="invalid_draft_max_model_len"):
        sim_bridge.export_sim_case(deepcopy(raw_out), runtime_overrides={"draft_max_model_len": True})


def test_structure_ingress_reads_canonical_geometry_and_forwards_media_tokens(monkeypatch):
    from mindie_profiler.structure_mapping import _seal_digest

    case = _minimal_case()
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
        resolve_case_geometry(
            case, phase="prefill", tokens=64, sequences=1, context=0,
            media_tokens_per_sequence=-1,
        )

    seen_calls: list[dict] = []

    def _fake_export(case_doc, **kwargs):
        seen_calls.append(dict(kwargs))
        doc = {
            "schema_version": "mindie-model-structure/1",
            "nodes": [{
                "node_id": "n0", "replica": "0", "stage": "0",
                "phase": kwargs["phase"], "layer": 0,
            }],
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

    fake_pkg = ModuleType("mindie_sim")
    fake_structure = ModuleType("mindie_sim.structure")
    fake_structure.export_structure = _fake_export  # type: ignore[attr-defined]
    fake_pkg.structure = fake_structure  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mindie_sim", fake_pkg)
    monkeypatch.setitem(sys.modules, "mindie_sim.structure", fake_structure)

    _export_structure(case, geom)
    assert seen_calls[-1]["media_tokens_per_sequence"] == 256

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

    # Legacy mindie-sim lacking media_tokens_per_sequence fails honestly.
    def _legacy_export(case_doc, *, phase, tokens, context=0, sequences=1, scope="model", source=None):
        return {"ok": True}

    fake_structure.export_structure = _legacy_export  # type: ignore[attr-defined]
    with pytest.raises(ProfilerUsageError, match="media_tokens_per_sequence"):
        _export_structure(case, geom)


def test_parallel_overrides_read_full_env_and_cli_keys():
    env_parsed = _parallel_overrides(
        {}, {}, {"TP": "4", "DCP": "2", "PCP": "2"}, {}, {}, {}, "", None, {},
    )
    assert env_parsed["tp"] == 4
    assert env_parsed["cp"] == 2
    assert env_parsed["pcp"] == 2

    cmd_parsed = _parallel_overrides(
        {}, {}, {}, {}, {}, {},
        "vllm serve m --tensor-parallel-size 2 "
        "--decode-context-parallel-size 2 --prefill-context-parallel-size 2",
        None, {},
    )
    assert cmd_parsed["cp"] == 2 and cmd_parsed["pcp"] == 2
