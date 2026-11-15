"""Portable behavioral tests for deployed weight header and quantization mapping."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STRUCT_DIR = ROOT / "examples" / "structure"
MODULE_PATH = STRUCT_DIR / "fleet_weight_quantization.py"
if str(STRUCT_DIR) not in sys.path:
    sys.path.insert(0, str(STRUCT_DIR))


def _load():
    spec = importlib.util.spec_from_file_location("fleet_weight_quantization", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _isolated_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    os.environ.pop("MINDIE_SIM_SOURCE", None)


def _synthetic_review_row() -> dict:
    return {
        "model": "GLM-5.1-w4a4c8-mxfp4",
        "host": "synthetic-host",
        "source_url": "file:///mnt/weight/GLM-5.1-w4a4c8-mxfp4",
        "cfg_sha256": "11" * 32,
        "quant_sha256": "22" * 32,
        "index_sha256": "33" * 32,
        "header_manifest_sha256": "44" * 32,
        "header_bytes_read": 4096,
        "native_declared_groups": {"FLOAT|F32": 2, "W8A8_MXFP8|F8_E4M3": 1, "W4A4_MXFP4|U8": 1},
        "module_types": {
            "model.layers.*.input_layernorm.weight": {"FLOAT|F32": 2},
            "model.layers.*.self_attn.o_proj.weight": {"W8A8_MXFP8|F8_E4M3": 1},
        },
        "layer3_modules": {
            "model.layers.3.input_layernorm.weight": ["FLOAT", "F32", [4], "weights.safetensors"],
            "model.layers.3.self_attn.o_proj.weight": ["W8A8_MXFP8", "F8_E4M3", [2, 4], "weights.safetensors"],
        },
    }


def _shard_header(tensors: list[tuple[str, str, list[int]]]) -> bytes:
    header: dict[str, dict] = {}
    offset = 0
    width = {"F32": 4, "BF16": 2, "F8_E4M3": 1, "U8": 1}
    for name, dtype, shape in tensors:
        numel = 1
        for dim in shape:
            numel *= dim
        nbytes = numel * width[dtype]
        header[name] = {"dtype": dtype, "shape": list(shape), "data_offsets": [offset, offset + nbytes]}
        offset += nbytes
    return json.dumps(header, separators=(",", ":")).encode()


def _write_deployment(root: Path, tensors: list[tuple[str, str, list[int]]], schemes: dict[str, str]) -> bytes:
    root.mkdir(parents=True, exist_ok=True)
    (root / "config.json").write_text(json.dumps({"model_type": "tiny", "dtype": "bfloat16"}), encoding="utf-8")
    description = {"group_size": 32, "model_quant_type": "W4A4_MXFP4"}
    description.update(schemes)
    (root / "quant_model_description.json").write_text(json.dumps(description), encoding="utf-8")
    weight_map = {name: "weights.safetensors" for name, _dtype, _shape in tensors}
    (root / "quant_model_weights.safetensors.index.json").write_text(
        json.dumps({"metadata": {}, "weight_map": weight_map, "total_size": 1}),
        encoding="utf-8",
    )
    blob = _shard_header(tensors)
    (root / "weights.safetensors").write_bytes(struct.pack("<Q", len(blob)) + blob + b"PAYLOAD_NOT_READ" + b"\xef" * 64)
    return blob


def _manifest(blob: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(b"weights.safetensors\0" + hashlib.sha256(blob).digest())
    return digest.hexdigest()


def test_header_perturbation_preserves_unrelated_bytes_and_skips_payload(tmp_path: Path) -> None:
    quant = _load()
    schemes = {
        "model.layers.3.input_layernorm.weight": "FLOAT",
        "model.layers.3.self_attn.o_proj.weight": "W8A8_MXFP8",
        "model.layers.3.mlp.experts.0.gate_proj.weight": "W4A4_MXFP4",
    }
    original_tensors = [
        ("model.layers.3.input_layernorm.weight", "F32", [4]),
        ("model.layers.3.self_attn.o_proj.weight", "F8_E4M3", [2, 4]),
        ("model.layers.3.mlp.experts.0.gate_proj.weight", "U8", [2, 2]),
    ]
    root = tmp_path / "local-a"
    blob = _write_deployment(root, original_tensors, schemes)
    first = quant.load_deployed_module_quant(root)
    assert first["status"] == "mapped"
    assert first["header_binding"]["origin"] == "local_shard_header"
    assert first["header_binding"]["manifest_sha256"] == _manifest(blob)
    assert first["units"]["weight_payload_bytes_read"] == 0
    assert first["units"]["header_bytes_read"] == len(blob)
    read = first["header_binding"]["shard_reads"][0]
    assert read["payload_bytes_read"] == 0
    assert read["file_bytes"] > read["prefix_bytes"] + read["header_bytes"]
    assert b"PAYLOAD_NOT_READ" in (root / "weights.safetensors").read_bytes()
    assert b"PAYLOAD_NOT_READ" not in json.dumps(first).encode()
    by_key = {item["key"]: item for item in first["header_tensors"]}
    assert by_key["model.layers.3.input_layernorm.weight"]["physical_bytes"] == 16
    assert by_key["model.layers.3.self_attn.o_proj.weight"]["physical_bytes"] == 8
    assert by_key["model.layers.3.mlp.experts.0.gate_proj.weight"]["physical_bytes"] == 4
    assert by_key["model.layers.3.mlp.experts.0.gate_proj.weight"]["logical_elements"] == 8
    assert by_key["model.layers.3.mlp.experts.0.gate_proj.weight"]["packed"] is True

    decoy = tmp_path / "decoy.jsonl"
    decoy.write_text(json.dumps({
        "model": root.name,
        "cfg_sha256": first["sources"]["config"]["sha256"],
        "quant_sha256": first["sources"]["quant_model_description"]["sha256"],
        "index_sha256": first["sources"]["weight_index"]["sha256"],
        "header_manifest_sha256": "ab" * 32,
        "host": "decoy-host",
        "native_declared_groups": {"FLOAT|BF16": 1},
        "module_types": {"model.layers.*.input_layernorm.weight": {"FLOAT|BF16": 1}},
        "layer3_modules": {"model.layers.3.input_layernorm.weight": ["FLOAT", "BF16", [4], "weights.safetensors"]},
    }) + "\n", encoding="utf-8")
    with_decoy = quant.load_deployed_module_quant(root, header_archive=decoy)
    decoy_norm = next(item for item in with_decoy["header_tensors"] if item["key"].endswith("input_layernorm.weight"))
    assert with_decoy["header_binding"]["origin"] == "local_shard_header"
    assert decoy_norm["stored_dtype"] == "F32"
    assert decoy_norm["physical_bytes"] == 16
    assert with_decoy["units"]["weight_payload_bytes_read"] == 0

    perturbed_tensors = [
        ("model.layers.3.input_layernorm.weight", "F32", [4]),
        ("model.layers.3.self_attn.o_proj.weight", "BF16", [2, 4]),
        ("model.layers.3.mlp.experts.0.gate_proj.weight", "U8", [2, 2]),
    ]
    other = tmp_path / "local-b"
    other_blob = _write_deployment(other, perturbed_tensors, schemes)
    second = quant.load_deployed_module_quant(other)
    second_keys = {item["key"]: item for item in second["header_tensors"]}
    assert second_keys["model.layers.3.input_layernorm.weight"]["physical_bytes"] == 16
    assert second_keys["model.layers.3.input_layernorm.weight"]["stored_dtype"] == "F32"
    assert second_keys["model.layers.3.mlp.experts.0.gate_proj.weight"]["physical_bytes"] == 4
    assert second_keys["model.layers.3.mlp.experts.0.gate_proj.weight"]["logical_elements"] == 8
    assert second_keys["model.layers.3.self_attn.o_proj.weight"]["stored_dtype"] == "BF16"
    assert second_keys["model.layers.3.self_attn.o_proj.weight"]["physical_bytes"] == 16
    assert second["header_binding"]["manifest_sha256"] == _manifest(other_blob)
    assert second["header_binding"]["manifest_sha256"] != first["header_binding"]["manifest_sha256"]
    assert second["units"]["weight_payload_bytes_read"] == 0


def test_description_reader_bounds_small_files_and_streams_over_50mib(tmp_path: Path) -> None:
    quant = _load()
    small = tmp_path / "small"
    small.mkdir()
    (small / "quant_model_description.json").write_text(
        json.dumps({"group_size": 32, "model.layers.1.input_layernorm.weight": "FLOAT"}),
        encoding="utf-8",
    )
    small_mapped = quant.load_deployed_module_quant(small)
    assert small_mapped["sources"]["quant_model_description"]["read_mode"] == "bounded"
    assert small_mapped["status"] == "mapped"
    assert small_mapped["weight_counts"]["FLOAT"] == 1
    assert small_mapped["units"]["weight_payload_bytes_read"] == 0

    large = tmp_path / "large"
    large.mkdir()
    path = large / "quant_model_description.json"
    pad = 50 * 1024 * 1024 + 64
    with path.open("w", encoding="utf-8") as handle:
        handle.write('{"tail_marker":7,"model.layers.1.input_layernorm.weight":"FLOAT","pad":"')
        remaining = pad
        chunk = "b" * (1 << 20)
        while remaining:
            take = min(remaining, len(chunk))
            handle.write(chunk[:take])
            remaining -= take
        handle.write('"}')
    assert path.stat().st_size > 50 * 1024 * 1024
    large_mapped = quant.load_deployed_module_quant(large)
    assert large_mapped["sources"]["quant_model_description"]["read_mode"] == "stream"
    assert large_mapped["status"] == "mapped"
    assert large_mapped["header"]["tail_marker"] == 7
    assert large_mapped["weight_counts"]["FLOAT"] == 1
    assert large_mapped["units"]["weight_payload_bytes_read"] == 0


def test_bf16_directory_without_description_is_not_a_float_map(tmp_path: Path) -> None:
    quant = _load()
    bf16_dir = tmp_path / "bf16-only"
    bf16_dir.mkdir()
    (bf16_dir / "config.json").write_text(json.dumps({"model_type": "tiny", "dtype": "bfloat16"}), encoding="utf-8")
    mapped = quant.load_deployed_module_quant(bf16_dir)
    assert mapped["status"] == "description_absent"
    assert mapped["weight_counts"] is None
    assert mapped["modules"] == []
    assert mapped["architecture"]["dtype"] == "bfloat16"
    assert "config dtype is not a per-tensor map" in mapped["unknowns"][0]
    assert quant.project_weight_work_units(mapped)["source_eligible"] is False


def test_failed_provenance_write_keeps_the_previous_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    quant = _load()
    document = quant.provenance_from_review_row(_synthetic_review_row())
    dest = tmp_path / "header_provenance.json"
    quant.write_header_provenance(dest, document)
    before = dest.read_bytes()
    invalid = json.loads(before)
    invalid["identity"]["quant_sha256"] = "not-a-sha"
    with pytest.raises(ValueError):
        quant.write_header_provenance(dest, invalid)
    assert dest.read_bytes() == before
    assert not dest.with_name(dest.name + ".partial").exists()
    import fleet_weight_headers as headers

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(headers.os, "replace", fail_replace)
    changed = json.loads(before)
    changed["identity"]["index_sha256"] = "cd" * 32
    with pytest.raises(OSError, match="replace failed"):
        quant.write_header_provenance(dest, changed)
    assert dest.read_bytes() == before
    assert not dest.with_name(dest.name + ".partial").exists()


def test_optional_sibling_mismatch_does_not_drop_the_scheme(tmp_path: Path) -> None:
    quant = _load()
    root = tmp_path / "tiny-opt"
    root.mkdir()
    (root / "config.json").write_text(json.dumps({"model_type": "tiny", "dtype": "bfloat16"}), encoding="utf-8")
    (root / "quant_model_description.json").write_text(
        json.dumps({"model_quant_type": "W8A8_MXFP8", "model.layers.1.input_layernorm.weight": "FLOAT"}),
        encoding="utf-8",
    )
    (root / "quant_model_weights.safetensors.index.json").write_text(
        json.dumps({"metadata": {"total_size": 4}}),
        encoding="utf-8",
    )
    bare = quant.load_deployed_module_quant(root)
    assert bare["status"] == "mapped"
    assert bare["weight_counts"]["FLOAT"] == 1
    document = quant.provenance_from_review_row(_synthetic_review_row())
    document["source"]["directory"] = root.name
    document["identity"]["config_sha256"] = "11" * 32
    document["identity"]["quant_sha256"] = "22" * 32
    document["identity"]["index_sha256"] = "33" * 32
    sidecar = root / "header_provenance.json"
    quant.write_header_provenance(sidecar, document)
    optional = quant.load_deployed_module_quant(root)
    assert optional["status"] == "mapped"
    assert optional["weight_counts"]["FLOAT"] == 1
    assert optional["header_binding"]["origin"] == "absent"
    assert optional["header_binding"]["flag"] == "optional_provenance_not_applied"
    assert optional["weight_stored_counts"] is None
    explicit = quant.load_deployed_module_quant(root, header_source=sidecar)
    assert explicit["status"] == "ineligible"
    assert explicit["header_binding"]["reason"] == "metadata_mismatch"
    sidecar.write_text("{not-json", encoding="utf-8")
    corrupt = quant.load_deployed_module_quant(root)
    assert corrupt["status"] == "mapped"
    assert corrupt["weight_counts"]["FLOAT"] == 1
    assert corrupt["header_binding"]["flag"] == "optional_provenance_not_applied"
    document["identity"]["config_sha256"] = bare["sources"]["config"]["sha256"]
    document["identity"]["quant_sha256"] = bare["sources"]["quant_model_description"]["sha256"]
    document["identity"]["index_sha256"] = bare["sources"]["weight_index"]["sha256"]
    quant.write_header_provenance(sidecar, document)
    matched = quant.load_deployed_module_quant(root)
    assert matched["status"] == "mapped"
    assert matched["header_binding"]["origin"] == "acquired_header_archive"
    assert matched["header_binding"]["full_tensor_headers"] is False
    assert matched["header_binding"]["layer_coverage"] == "subset"
    assert matched["header_tensors"] == []
    layernorm = next(row for row in matched["modules"] if row["category"] == "model.layers.input_layernorm" and row["role"] == "weight")
    assert layernorm["count"] == 1
    assert layernorm["stored_dtype"] is None
    assert layernorm["byte_status"] == "header_count_disagrees"
