"""Focused source-binding/acceptance-input tests for the profiler L4 pair."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
pytest.importorskip("mindie_sim")

import hf_benchmark_requests as hfb  # noqa: E402
import zero_shot_actual_entry as zsa  # noqa: E402
import zero_shot_piecewise_validation as zsv  # noqa: E402
import zero_shot_source_binding as zsb  # noqa: E402

BENCH_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_glm53flash_tp8_c4_p8k.json"


@pytest.fixture(autouse=True)
def _clear_l4_index_cache():
    if hasattr(hfb._zero_shot_l4_pair, "_paths"):
        delattr(hfb._zero_shot_l4_pair, "_paths")
    yield
    if hasattr(hfb._zero_shot_l4_pair, "_paths"):
        delattr(hfb._zero_shot_l4_pair, "_paths")


def _source(tmp_path: Path) -> tuple[Path, str]:
    config = tmp_path / "GLM-5.3-W8A8C8-mxfp8" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        json.dumps(
            {
                "model_type": "deepseek_v3",
                "architectures": ["DeepseekV3ForCausalLM"],
                "hidden_size": 2048,
                "num_hidden_layers": 2,
                "first_k_dense_replace": 0,
                "num_attention_heads": 16,
                "num_key_value_heads": 16,
                "q_lora_rank": 512,
                "kv_lora_rank": 512,
                "qk_nope_head_dim": 128,
                "qk_rope_head_dim": 64,
                "v_head_dim": 128,
                "intermediate_size": 4096,
                "moe_intermediate_size": 1024,
                "n_routed_experts": 16,
                "num_experts_per_tok": 4,
                "n_shared_experts": 1,
                "vocab_size": 32000,
                "max_position_embeddings": 16384,
            }
        ),
        encoding="utf-8",
    )
    return config, hashlib.sha256(config.read_bytes()).hexdigest()


def _case(tmp_path: Path) -> Path:
    case = tmp_path / "case.json"
    case.write_text(json.dumps({"model": {}}), encoding="utf-8")
    return case


def _bench_row(config: Path, declared_sha: str, *, cell_id: str = "bench_cell") -> dict:
    return {
        "cell_id": cell_id,
        "dataset": "bench",
        "phase": "prefill",
        "model_case": str(BENCH_CASE),
        "model_label": "GLM-5.3/W8A8-MXFP8",
        "prompt_tokens": 1024,
        "concurrency": 1,
        "max_tokens": 1,
        "tp": 1,
        "dp": 16,
        "ep": 16,
        "source_config": str(config),
        "source_config_sha256": declared_sha,
        "require_source": True,
        "hardware_tier": "A5",
    }


def _install_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    cell_id: str,
    *,
    predictor=None,
    patch_predictor: bool = True,
) -> list:
    observation = tmp_path / "observation.json"
    observation.write_text("{}", encoding="utf-8")
    calls: list = []

    def _no_interface(_row):
        raise ValueError("synthetic: no request interface")

    def _predict(spec):
        calls.append(spec)
        if predictor is not None:
            return predictor(spec)
        return SimpleNamespace(ttft_ms=12.5, notes=())

    monkeypatch.setattr(hfb, "_l4_interface", _no_interface)
    monkeypatch.setattr(zsa, "_index", lambda _roots: {cell_id: str(observation)})
    monkeypatch.setattr(
        hfb.hf_benchmark_gate,
        "singleton_request_ttft",
        lambda _raw, _phase: {"eligible": True, "observed_ms": 12.5, "key": "request:0"},
    )
    if patch_predictor:
        monkeypatch.setattr(zsv, "predict_cell", _predict)
    return calls


def test_declared_digest_mismatch_is_a_typed_identity_gap(tmp_path: Path) -> None:
    config, actual = _source(tmp_path)
    case = _case(tmp_path)
    spec = zsv.CellSpec(
        "cell_a", "bench", "prefill", case, "unresolved", 1, 1, 1, 1, 1, 1, 1,
        source_config=config, source_config_sha256="f" * 64,
    )
    with pytest.raises(zsb.SourceConfigDigestMismatch) as caught:
        zsb._raw_case_base(spec)
    assert isinstance(caught.value, ValueError)
    assert caught.value.declared_sha256 == "f" * 64
    assert caught.value.actual_sha256 == actual
    assert caught.value.path == config
    assert str(caught.value) == f"source_config_sha256_mismatch:{actual}"


def test_cell_from_dict_propagates_the_resolved_digest_gap(tmp_path: Path) -> None:
    config, actual = _source(tmp_path)
    row = _bench_row(config, "f" * 64)
    cell = zsv.cell_from_dict(row)
    assert cell.spec.source_reject_reason == "source_config_sha256_mismatch"
    assert cell.spec.source_file_sha256 == actual
    assert cell.spec.source_config_sha256 == actual


def test_bench_direct_parser_preserves_wrong_sha_and_missing_path_reasons(tmp_path: Path) -> None:
    config, actual = _source(tmp_path)
    wrong = zsv.cell_from_dict(_bench_row(config, "f" * 64)).spec
    assert wrong.source_reject_reason == "source_config_sha256_mismatch"
    assert wrong.source_file_sha256 == actual
    rejected = zsv.predict_cell(wrong)
    assert rejected.layers == 0
    assert "source_override_rejected:source_config_sha256_mismatch" in rejected.notes
    missing = _bench_row(tmp_path / "never-existed" / "config.json", actual)
    absent = zsv.cell_from_dict(missing).spec
    assert absent.source_reject_reason == "source_override_path_invalid"
    assert absent.source_file_sha256 == ""


def test_bench_jsonl_validation_uses_same_resolved_file(tmp_path: Path) -> None:
    config, actual = _source(tmp_path)
    row = _bench_row(config, actual)
    alias = dict(row)
    alias.pop("source_config", None)
    alias["model_config_path"] = str(config)
    cells_path = tmp_path / "cells.jsonl"
    cells_path.write_text(
        "\n".join(json.dumps(item) for item in (row, alias)) + "\n", encoding="utf-8")
    loaded = zsv.load_benchmark_jsonl(cells_path, roots=[tmp_path])
    assert len(loaded) == 2
    for cell in loaded:
        assert cell.spec.source_file_sha256 == actual
        assert cell.spec.source_config_sha256 == actual
        assert zsv._structure_fingerprint(cell.spec) == zsv._structure_fingerprint(loaded[0].spec)


def test_bench_real_parser_matching_declaration_prices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, actual = _source(tmp_path)
    calls = _install_gate(monkeypatch, tmp_path, "bench_cell")
    bundle = hfb._zero_shot_l4_pair(_bench_row(config, actual))
    assert bundle["source_raw"] == "bound"
    assert bundle.get("reason", "") == ""
    assert bundle["prediction"]["boundary_ms"] == pytest.approx(12.5)
    assert bundle["declared_config_sha256"] == actual
    assert bundle["source_file_sha256"] == actual
    assert bundle["source_config_sha256"] == actual
    assert bundle["source_deploy_sha256"] == ""
    assert bundle["source_origin"] == "source_file"
    assert len(calls) == 1


def test_bench_real_parser_contradiction_never_prices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, actual = _source(tmp_path)
    calls = _install_gate(monkeypatch, tmp_path, "bench_cell")
    bundle = hfb._zero_shot_l4_pair(_bench_row(config, "f" * 64))
    assert bundle["reason"] == "source_config_sha256_mismatch"
    assert bundle["source_raw"] == "uncertain"
    assert bundle["declared_config_sha256"] == "f" * 64
    assert bundle["source_file_sha256"] == actual
    assert bundle["source_config_sha256"] == actual
    assert bundle["source_origin"] == "source_file"
    assert bundle["prediction"]["source_sha256"] == "f" * 64
    assert "boundary_ms" not in bundle["prediction"]
    observation = bundle["observation"]
    assert observation["source"]["sha256"] == actual
    assert observation["source"]["path"] == str(config)
    assert observation["measurement_source"]["sha256"] != actual
    assert calls == []


def test_bench_real_parser_missing_declaration_is_a_path_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, actual = _source(tmp_path)
    calls = _install_gate(monkeypatch, tmp_path, "bench_cell")
    row = _bench_row(tmp_path / "never-existed" / "config.json", actual)
    bundle = hfb._zero_shot_l4_pair(row)
    assert bundle["reason"] == "source_override_path_invalid"
    assert bundle["source_raw"] == "missing"
    assert bundle["declared_config_sha256"] == actual
    assert bundle["source_file_sha256"] == ""
    assert "prediction" not in bundle
    assert calls == []


def test_same_basename_in_different_directories_keeps_own_file_source(tmp_path: Path) -> None:
    config, actual = _source(tmp_path / "first")
    second = tmp_path / "second" / "GLM-5.3-W8A8C8-mxfp8" / "config.json"
    second.parent.mkdir(parents=True)
    shutil.copyfile(config, second)
    second.write_text(second.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    second_sha = hashlib.sha256(second.read_bytes()).hexdigest()
    assert second_sha != actual
    first_spec = zsv.cell_from_dict(_bench_row(config, actual, cell_id="bench_first")).spec
    second_spec = zsv.cell_from_dict(_bench_row(second, second_sha, cell_id="bench_second")).spec
    assert first_spec.source_config == config
    assert second_spec.source_config == second
    assert first_spec.source_config_sha256 == actual
    assert second_spec.source_config_sha256 == second_sha
    assert zsv._structure_fingerprint(first_spec) != zsv._structure_fingerprint(second_spec)


def test_bench_real_parser_and_predictor_via_source_config_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, actual = _source(tmp_path)
    _install_gate(monkeypatch, tmp_path, "bench_cell", patch_predictor=False)
    bundle = hfb._zero_shot_l4_pair(_bench_row(config, actual))
    assert bundle["source_raw"] == "bound"
    assert bundle["prediction"]["status"] == "modeled"
    assert bundle["prediction"]["boundary_ms"] > 0
    assert bundle["prediction"]["source_config"] == str(config)
    assert bundle["prediction"]["source_file_sha256"] == actual
    assert bundle["prediction"]["source_sha256"] == actual
    assert bundle["prediction"]["source_config_sha256"] == actual
    assert bundle["prediction"]["source_deploy_sha256"] == ""
    direct = zsv.cell_from_dict(_bench_row(config, actual))
    assert direct.spec.source_file_sha256 == bundle["source_file_sha256"] == actual
    assert zsv._structure_fingerprint(direct.spec) == bundle["structure_fingerprint"]


def test_bench_source_and_model_config_aliases_share_file_fingerprint(tmp_path: Path) -> None:
    config, actual = _source(tmp_path)
    direct = _bench_row(config, actual)
    direct["source_file_sha256"] = actual
    alias = dict(direct)
    alias.pop("source_config", None)
    alias["model_config_path"] = str(config)
    direct_spec = zsv.cell_from_dict(direct).spec
    alias_spec = zsv.cell_from_dict(alias).spec
    assert direct_spec.source_config == alias_spec.source_config == config
    assert direct_spec.source_config_sha256 == alias_spec.source_config_sha256 == actual
    assert direct_spec.source_file_sha256 == alias_spec.source_file_sha256 == actual
    assert zsv._structure_fingerprint(direct_spec) == zsv._structure_fingerprint(alias_spec)


def test_bench_real_parser_and_predictor_via_model_config_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, actual = _source(tmp_path)
    _install_gate(monkeypatch, tmp_path, "bench_cell", patch_predictor=False)
    row = _bench_row(config, actual)
    row.pop("source_config", None)
    row["model_config_path"] = str(config)
    bundle = hfb._zero_shot_l4_pair(row)
    assert bundle["source_raw"] == "bound"
    assert bundle["prediction"]["status"] == "modeled"
    assert bundle["prediction"]["boundary_ms"] > 0
    assert bundle["prediction"]["source_config"] == str(config)
    assert bundle["prediction"]["source_file_sha256"] == actual
    assert bundle["prediction"]["source_config_sha256"] == actual
    assert bundle["prediction"]["source_deploy_sha256"] == ""


def test_l4_pair_keeps_a_pathless_digest_as_an_invalid_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, actual = _source(tmp_path)
    calls = _install_gate(monkeypatch, tmp_path, "bench_cell")
    row = {
        "cell_id": "bench_cell",
        "dataset": "bench",
        "phase": "prefill",
        "model_case": str(BENCH_CASE),
        "hardware_tier": "A5",
        "source_config_sha256": actual,
    }
    bundle = hfb._zero_shot_l4_pair(row)
    assert bundle["reason"] == "source_override_path_invalid"
    assert bundle["source_raw"] == "missing"
    assert bundle["declared_config_sha256"] == actual
    assert "prediction" not in bundle
    assert calls == []


def test_direct_digest_mismatch_precedes_parser_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, actual = _source(tmp_path)
    calls = _install_gate(monkeypatch, tmp_path, "bench_cell")
    monkeypatch.setattr(
        zsv,
        "cell_from_dict",
        lambda _row: (_ for _ in ()).throw(ValueError("broken case payload")),
    )
    bundle = hfb._zero_shot_l4_pair(_bench_row(config, "f" * 64))
    assert bundle["reason"] == "source_config_sha256_mismatch"
    assert bundle["source_raw"] == "uncertain"
    assert bundle["declared_config_sha256"] == "f" * 64
    assert bundle["source_file_sha256"] == actual
    assert bundle["source_config_sha256"] == actual
    assert bundle["diagnostics"] == [
        "prediction_case_unparseable:ValueError:broken case payload"
    ]
    assert "prediction" not in bundle
    assert calls == []


def test_l4_pair_keeps_genuine_parse_gap_as_prediction_case_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, actual = _source(tmp_path)
    calls = _install_gate(monkeypatch, tmp_path, "bench_cell")
    monkeypatch.setattr(
        zsv,
        "cell_from_dict",
        lambda _row: (_ for _ in ()).throw(ValueError("broken case payload")),
    )
    bundle = hfb._zero_shot_l4_pair(_bench_row(config, actual))
    assert bundle["reason"] == "prediction_case_absent"
    assert bundle["source_raw"] == "missing"
    assert bundle["diagnostics"] == [
        "prediction_case_unparseable:ValueError:broken case payload"
    ]
    assert "prediction" not in bundle
    assert calls == []
