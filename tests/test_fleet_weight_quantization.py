"""Deployed sidecar maps for GLM 5.1 W4 and GLM 5.3 W8/W4.

The counts are the .weight rows of each directory's quant_model_description.
The same config sha256 on the two 5.3 directories must not collapse the maps.
Stored dtype and byte sizes come from a local safetensors header or from a
declared header archive whose directory name and metadata hashes match.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import resource
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "examples" / "structure" / "fleet_weight_quantization.py"
DATA = Path("/Volumes/data/mindie-sim-data/a5/weights-metadata-20261108")
GLM51_W4 = DATA / "GLM-5.1-w4a4c8-mxfp4"
GLM53_W8 = DATA / "GLM-5.3-W8A8C8-mxfp8"
GLM53_W4 = DATA / "GLM-5.3-w4a4c8-mxfp4"
GLM53_BF16 = DATA / "GLM-5.3-BF16"
KIMI_ROOT = DATA / "Kimi-K3-w4a8-mxfp-root"
KIMI_QUAROT = DATA / "Kimi-K3-w4a8-mxfp-quarot"
ARCHIVE = Path("/tmp/mindie-7337-20261111-1457/model_original_weight_headers.jsonl")


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


def test_glm51_w4_weight_counts_exclude_scales_and_the_header_label() -> None:
    quant = _load()
    mapped = quant.load_deployed_module_quant(GLM51_W4)
    assert mapped["status"] == "mapped"
    assert mapped["weight_counts"] == {"W4": 58368, "W8": 632, "FLOAT": 717}
    assert mapped["parameter_counts"]["scale"]["W4A4_MXFP4"] == 58368
    assert mapped["parameter_counts"]["scale"]["W8A8_MXFP8"] == 632
    assert mapped["parameter_counts"]["bias"]["FLOAT"] == 79
    assert mapped["header"]["model_quant_type"] == "W4A4_MXFP4"
    assert mapped["header"]["group_size"] == 32
    assert mapped["units"]["weight_payload_bytes_read"] == 0
    assert mapped["units"]["per_tensor_status"] == "unknown"
    assert mapped["kv"]["cache_quant_status"] == "unknown"
    assert mapped["kv"]["kv_lora_rank"] == 512
    mtp_categories = {row["category"] for row in mapped["mtp"]["modules"]}
    assert mapped["mtp"]["num_nextn_predict_layers"] == 1
    assert mapped["mtp"]["index_share_for_mtp_iteration"] is None
    assert "model.layers.eh_proj" in mtp_categories
    assert mapped["architecture"]["selects_weights"] is False
    assert mapped["sources"]["quant_model_description"]["read_mode"] == "bounded"
    assert mapped["header_binding"]["origin"] == "absent"
    assert mapped["header_binding"]["remote_connect"] is False
    assert mapped["weight_stored_counts"] is None
    assert mapped["header_tensors"] == []
    projected = quant.project_weight_work_units(mapped)
    assert projected["stored_dtype_bound"] is False
    assert projected["source_eligible"] is True
    assert projected["weight_counts"]["FLOAT"] == 717
    assert projected["tensors"] == []
    assert all(row["stored_dtype"] is None for row in projected["modules"])


def test_same_config_sha_keeps_glm53_w8_and_w4_maps_apart() -> None:
    quant = _load()
    w8 = quant.load_deployed_module_quant(GLM53_W8)
    w4 = quant.load_deployed_module_quant(GLM53_W4)
    assert w8["weight_counts"] == {"W4": 0, "W8": 58943, "FLOAT": 546}
    assert w4["weight_counts"] == {"W4": 58368, "W8": 575, "FLOAT": 546}
    assert w8["architecture"]["config_sha256"] == w4["architecture"]["config_sha256"]
    assert w8["sources"]["quant_model_description"]["sha256"] != w4["sources"]["quant_model_description"]["sha256"]
    assert w8["sources"]["weight_index"]["total_size_bytes"] != w4["sources"]["weight_index"]["total_size_bytes"]
    assert w8["architecture"]["config_sha256"] != quant.load_deployed_module_quant(GLM51_W4)["architecture"]["config_sha256"]
    attention = w8["kv"]["attention_quant_type"]
    assert attention == [{"scheme": "MXFP8_DYNAMIC", "count": 71, "layer_count": 71}]
    declarations = w8["parameter_counts"]["declaration"]
    assert declarations["FP8_DYNAMIC"] == 16
    assert declarations["MXFP8_DYNAMIC"] == 71
    assert "INT8_DYNAMIC" not in declarations
    assert w8["header"]["indexer_quant_type"] == "INT8_DYNAMIC"
    assert w8["mtp"]["index_share_for_mtp_iteration"] is True
    assert all(row["scheme"] == "FLOAT" for row in w8["mtp"]["modules"])


def _archive_rows() -> list[dict]:
    rows = []
    with ARCHIVE.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _archive_row(model: str) -> dict:
    return next(row for row in _archive_rows() if row.get("model") == model)


def _module(bound: dict, category: str) -> dict:
    return next(row for row in bound["modules"] if row["category"] == category)


def _tensor(bound: dict, suffix: str) -> dict:
    return next(row for row in bound["tensors"] if row["key"].endswith(suffix) and ".layers.3." in row["key"])


def test_loader_does_not_hardcode_review_labels() -> None:
    texts = [
        MODULE_PATH.read_text(encoding="utf-8"),
        MODULE_PATH.with_name("fleet_weight_headers.py").read_text(encoding="utf-8"),
    ]
    assert len(texts[0].splitlines()) < 800
    for text in texts:
        for banned in ("320", "397", "206", "340", "177.25.21.1", "rack06", "model_original_weight_headers", "socket"):
            assert banned not in text
        assert ".read()" not in text
        assert "lru_cache" not in text
    assert "no subprocess" in texts[0]


def test_end_to_end_consumer_binds_glm51_header_dtypes_and_bytes() -> None:
    quant = _load()
    row = _archive_row("GLM-5.1-w4a4c8-mxfp4")
    assert row["native_declared_groups"]["FLOAT|BF16"] == 320
    assert row["native_declared_groups"]["FLOAT|F32"] == 397
    bound = quant.bind_deployed_weight_units(GLM51_W4, header_archive=ARCHIVE)
    raw = quant.load_deployed_module_quant(GLM51_W4, header_archive=ARCHIVE)
    assert bound["status"] == "mapped"
    assert bound["stored_dtype_bound"] is True
    assert bound["source_eligible"] is True
    assert bound["origin"] == "acquired_header_archive"
    assert bound["flag"] == "archive_lacks_tensor_headers_metadata_matches"
    assert bound["remote_connect"] is False
    assert bound["weight_payload_bytes_read"] == 0
    assert raw["units"]["weight_payload_bytes_read"] == 0
    assert raw["units"]["header_bytes_read"] == 0
    assert raw["header_binding"]["full_tensor_headers"] is False
    assert raw["header_binding"]["local_shards"] is False
    assert raw["header_binding"]["metadata_matches_archive"] is True
    assert raw["header_binding"]["acquired_host"] == row["host"]
    assert raw["header_binding"]["manifest_sha256"] == row["header_manifest_sha256"]
    assert raw["header_binding"]["acquired_header_bytes"] == row["header_bytes_read"]
    assert bound["config_sha256"] == row["cfg_sha256"]
    assert bound["description_sha256"] == row["quant_sha256"]
    assert bound["index_sha256"] == row["index_sha256"]
    assert bound["weight_stored_counts"]["BF16"] == 320
    assert bound["weight_stored_counts"]["F32"] == 397
    assert bound["weight_stored_counts"]["F8_E4M3"] == row["native_declared_groups"]["W8A8_MXFP8|F8_E4M3"]
    assert bound["weight_stored_counts"]["U8"] == row["native_declared_groups"]["W4A4_MXFP4|U8"]
    norm = _module(bound, "model.layers.input_layernorm")
    gate = _module(bound, "model.layers.mlp.gate")
    kv_b = _module(bound, "model.layers.self_attn.kv_b_proj")
    o_proj = _module(bound, "model.layers.self_attn.o_proj")
    assert norm["stored_dtype"] == "F32"
    assert gate["stored_dtype"] == "BF16"
    assert kv_b["stored_dtype"] == "BF16"
    assert o_proj["stored_dtype"] == "F8_E4M3"
    assert norm["scheme"] == "FLOAT"
    assert norm["physical_bytes"] is None
    assert gate["physical_bytes"] is None
    assert norm["byte_status"] == "category_count_is_not_bytes"
    assert norm["count"] == row["module_types"]["model.layers.*.input_layernorm.weight"]["FLOAT|F32"]
    assert norm["count"] != 24576
    layernorm = _tensor(bound, "input_layernorm.weight")
    gate_tensor = _tensor(bound, "mlp.gate.weight")
    kv_tensor = _tensor(bound, "self_attn.kv_b_proj.weight")
    o_tensor = _tensor(bound, "self_attn.o_proj.weight")
    expert = _tensor(bound, "mlp.experts.0.gate_proj.weight")
    assert layernorm["stored_dtype"] == "F32"
    assert layernorm["element_bytes"] == 4
    assert layernorm["shape"] == [6144]
    assert layernorm["physical_bytes"] == 6144 * 4
    assert layernorm["logical_elements"] == 6144
    assert layernorm["packed"] is False
    assert layernorm["layer"] == 3
    assert layernorm["expert"] is None
    assert gate_tensor["stored_dtype"] == "BF16"
    assert gate_tensor["element_bytes"] == 2
    assert gate_tensor["physical_bytes"] == 256 * 6144 * 2
    assert gate_tensor["logical_elements"] == 256 * 6144
    assert kv_tensor["stored_dtype"] == "BF16"
    assert kv_tensor["physical_bytes"] == 28672 * 512 * 2
    assert o_tensor["stored_dtype"] == "F8_E4M3"
    assert o_tensor["element_bytes"] == 1
    assert o_tensor["physical_bytes"] == 6144 * 16384
    assert o_tensor["packed"] is False
    assert expert["stored_dtype"] == "U8"
    assert expert["packed"] is True
    assert expert["expert"] == 0
    assert expert["physical_bytes"] == 2048 * 3072
    assert expert["logical_elements"] == 2048 * 3072 * 2
    names: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            names.update(str(key) for key in value)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(bound)
    for banned in ("capture_id", "observed_ms", "elapsed", "tpot", "ttft"):
        assert banned not in names


def test_same_architecture_keeps_w4_and_w8_stored_dtypes_apart() -> None:
    quant = _load()
    w4 = quant.bind_deployed_weight_units(GLM53_W4, header_archive=ARCHIVE)
    w8 = quant.bind_deployed_weight_units(GLM53_W8, header_archive=ARCHIVE)
    assert w4["config_sha256"] == w8["config_sha256"]
    assert w4["description_sha256"] != w8["description_sha256"]
    assert w4["index_total_size_bytes"] != w8["index_total_size_bytes"]
    assert w4["weight_stored_counts"]["BF16"] == 206
    assert w4["weight_stored_counts"]["F32"] == 340
    assert w8["weight_stored_counts"]["BF16"] == 206
    assert w8["weight_stored_counts"]["F32"] == 340
    assert w4["weight_stored_counts"]["U8"] > 0
    assert "U8" not in w8["weight_stored_counts"]
    routed_w4 = _tensor(w4, "mlp.experts.0.gate_proj.weight")
    routed_w8 = _tensor(w8, "mlp.experts.0.gate_proj.weight")
    shared_w4 = _tensor(w4, "mlp.shared_experts.gate_proj.weight")
    assert routed_w4["stored_dtype"] == "U8"
    assert routed_w4["packed"] is True
    assert routed_w4["physical_bytes"] == 2048 * 3072
    assert routed_w4["logical_elements"] == 2048 * 3072 * 2
    assert routed_w8["stored_dtype"] == "F8_E4M3"
    assert routed_w8["packed"] is False
    assert routed_w8["physical_bytes"] == 2048 * 6144
    assert routed_w8["logical_elements"] == routed_w4["logical_elements"]
    assert routed_w4["physical_bytes"] != routed_w8["physical_bytes"]
    assert shared_w4["stored_dtype"] == "F8_E4M3"
    assert shared_w4["physical_bytes"] != routed_w4["physical_bytes"]
    for bound in (w4, w8):
        norm = _module(bound, "model.layers.input_layernorm")
        gate = _module(bound, "model.layers.mlp.gate")
        assert norm["stored_dtype"] == "F32"
        assert gate["stored_dtype"] == "BF16"
        assert _module(bound, "model.layers.self_attn.kv_b_proj")["stored_dtype"] == "BF16"
        assert _module(bound, "model.layers.self_attn.o_proj")["stored_dtype"] == "F8_E4M3"
        assert norm["physical_bytes"] is None
        assert norm["byte_status"] == "category_count_is_not_bytes"
        assert _tensor(bound, "input_layernorm.weight")["element_bytes"] == 4
        assert _tensor(bound, "mlp.gate.weight")["element_bytes"] == 2


def test_kimi_metadata_mismatch_is_not_source_eligible() -> None:
    quant = _load()
    host = _archive_row("Kimi-K3-w4a8-mxfp-quarot")
    root = quant.load_deployed_module_quant(KIMI_ROOT, header_archive=ARCHIVE)
    root_bound = quant.project_weight_work_units(root)
    assert root["status"] == "ineligible"
    assert root["header_binding"]["reason"] == "identity_name_mismatch"
    assert root["header_binding"]["source_eligible"] is False
    assert root["header_binding"]["rejected_archive_model"] == "Kimi-K3-w4a8-mxfp-quarot"
    assert root["header_binding"]["remote_connect"] is False
    assert root["weight_stored_counts"] is None
    assert root["header_tensors"] == []
    assert all(row.get("stored_dtype") is None for row in root["modules"])
    assert root["sources"]["config"]["sha256"] == host["cfg_sha256"]
    assert root["sources"]["quant_model_description"]["sha256"] == host["quant_sha256"]
    assert root["sources"]["weight_index"]["sha256"] == host["index_sha256"]
    assert root["sources"]["quant_model_description"]["read_mode"] == "bounded"
    assert root["sources"]["quant_model_description"]["bytes"] > 40 * 1024 * 1024
    assert root_bound["source_eligible"] is False
    assert root_bound["weight_counts"] is None
    assert root_bound["weight_stored_counts"] is None
    assert root_bound["tensors"] == []
    assert root_bound["modules"] == []
    quarot = quant.load_deployed_module_quant(KIMI_QUAROT, header_archive=ARCHIVE)
    quarot_bound = quant.project_weight_work_units(quarot)
    assert quarot["status"] == "ineligible"
    assert quarot["header_binding"]["reason"] == "metadata_mismatch"
    assert quarot["header_binding"]["source_eligible"] is False
    assert quarot["weight_stored_counts"] is None
    assert quarot["sources"]["config"]["sha256"] == host["cfg_sha256"]
    assert quarot["sources"]["quant_model_description"]["sha256"] != host["quant_sha256"]
    assert quarot["sources"]["weight_index"]["sha256"] != host["index_sha256"]
    assert quarot["sources"]["quant_model_description"]["read_mode"] == "bounded"
    assert quarot_bound["source_eligible"] is False
    assert quarot_bound["tensors"] == []
    assert quarot_bound["weight_stored_counts"] is None


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
    baseline = quant.bind_deployed_weight_units(GLM51_W4, header_archive=ARCHIVE)
    base_norm = _tensor(baseline, "input_layernorm.weight")
    base_o = _tensor(baseline, "self_attn.o_proj.weight")
    shape_archive = tmp_path / "shape.jsonl"
    _rewrite_glm51(shape_archive, lambda row: row["layer3_modules"].__setitem__(
        "model.layers.3.self_attn.o_proj.weight",
        ["W8A8_MXFP8", "BF16", [4, 4], row["layer3_modules"]["model.layers.3.self_attn.o_proj.weight"][3]],
    ))
    shaped = quant.bind_deployed_weight_units(GLM51_W4, header_archive=shape_archive)
    assert _tensor(shaped, "input_layernorm.weight")["physical_bytes"] == base_norm["physical_bytes"]
    assert _tensor(shaped, "input_layernorm.weight")["stored_dtype"] == "F32"
    assert _module(shaped, "model.layers.input_layernorm")["stored_dtype"] == "F32"
    assert _module(shaped, "model.layers.input_layernorm")["count"] == _module(baseline, "model.layers.input_layernorm")["count"]
    assert _tensor(shaped, "self_attn.o_proj.weight")["physical_bytes"] != base_o["physical_bytes"]
    assert _tensor(shaped, "self_attn.o_proj.weight")["stored_dtype"] == "BF16"
    assert _tensor(shaped, "self_attn.o_proj.weight")["physical_bytes"] == 32
    assert shaped["weight_payload_bytes_read"] == 0
    count_archive = tmp_path / "count.jsonl"
    _rewrite_glm51(count_archive, lambda row: row["module_types"].__setitem__(
        "model.layers.*.self_attn.o_proj.weight",
        {"W8A8_MXFP8|F8_E4M3": 1},
    ))
    counted = quant.bind_deployed_weight_units(GLM51_W4, header_archive=count_archive)
    assert _module(counted, "model.layers.input_layernorm")["stored_dtype"] == "F32"
    assert _module(counted, "model.layers.self_attn.o_proj")["stored_dtype"] is None
    assert _module(counted, "model.layers.self_attn.o_proj")["byte_status"] == "header_count_disagrees"
    assert _tensor(counted, "input_layernorm.weight")["physical_bytes"] == base_norm["physical_bytes"]
    assert _tensor(counted, "self_attn.o_proj.weight")["physical_bytes"] == base_o["physical_bytes"]
    assert counted["weight_payload_bytes_read"] == 0


def _rewrite_glm51(destination: Path, mutate) -> None:
    lines = []
    with ARCHIVE.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("model") == "GLM-5.1-w4a4c8-mxfp4":
                mutate(row)
            lines.append(json.dumps(row, sort_keys=True))
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    assert large_mapped["header"]["tail_marker"] == 7


def test_bf16_directory_without_description_is_not_a_float_map() -> None:
    quant = _load()
    mapped = quant.load_deployed_module_quant(GLM53_BF16)
    assert mapped["status"] == "description_absent"
    assert mapped["weight_counts"] is None
    assert mapped["modules"] == []
    assert mapped["architecture"]["dtype"] == "bfloat16"
    assert mapped["architecture"]["config_sha256"] == quant.load_deployed_module_quant(GLM53_W8)["architecture"]["config_sha256"]
    assert "config dtype is not a per-tensor map" in mapped["unknowns"][0]
    archived = quant.load_deployed_module_quant(GLM53_BF16, header_archive=ARCHIVE)
    assert archived["status"] == "description_absent"
    assert archived["weight_counts"] is None
    assert archived["modules"] == []
    assert archived["weight_stored_counts"] is None
    assert quant.project_weight_work_units(archived)["source_eligible"] is False


_MATCHING_DIRECTORIES = (
    "GLM-5.1-w4a4c8-mxfp4",
    "GLM-5.3-W8A8C8-mxfp8",
    "GLM-5.3-w4a4c8-mxfp4",
    "Qwen3.8-27B-w8a8-mxfp8-mtp",
    "Qwen3.5-397B-A17B-w4a4-mxfp4",
)


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def test_five_local_directories_match_archive_triples_and_kimi_does_not() -> None:
    matched = []
    for name in _MATCHING_DIRECTORIES:
        row = _archive_row(name)
        root = DATA / name
        assert _file_sha(root / "config.json") == row["cfg_sha256"]
        assert _file_sha(root / "quant_model_description.json") == row["quant_sha256"]
        assert _file_sha(root / "quant_model_weights.safetensors.index.json") == row["index_sha256"]
        matched.append(name)
    assert matched == list(_MATCHING_DIRECTORIES)
    host = _archive_row("Kimi-K3-w4a8-mxfp-quarot")
    local = DATA / "Kimi-K3-w4a8-mxfp-quarot"
    assert _file_sha(local / "config.json") == host["cfg_sha256"]
    assert _file_sha(local / "quant_model_description.json") != host["quant_sha256"]
    assert _file_sha(local / "quant_model_weights.safetensors.index.json") != host["index_sha256"]


def test_explicit_provenance_binds_subset_and_filename_is_not_a_sha(tmp_path: Path) -> None:
    quant = _load()
    row = _archive_row("GLM-5.1-w4a4c8-mxfp4")
    document = quant.provenance_from_review_row(row)
    assert document["schema"] == "fleet-weight-header-provenance/1"
    assert document["coverage"] == "role_aggregate_and_shaped_subset"
    assert document["full_tensor_headers"] is False
    assert document["source"]["host"] == row["host"]
    assert document["source"]["url"] == "file:///mnt/weight/GLM-5.1-w4a4c8-mxfp4"
    assert document["identity"]["config_sha256"] == row["cfg_sha256"]
    assert document["identity"]["quant_sha256"] == row["quant_sha256"]
    assert document["identity"]["index_sha256"] == row["index_sha256"]
    good = tmp_path / "GLM-5.1-w4a4c8-mxfp4.json"
    quant.write_header_provenance(good, document)
    bound = quant.bind_deployed_weight_units(GLM51_W4, header_source=good)
    assert bound["status"] == "mapped"
    assert bound["stored_dtype_bound"] is True
    assert bound["origin"] == "acquired_header_archive"
    assert bound["coverage"] == "role_aggregate_and_shaped_subset"
    assert bound["layer_coverage"] == "subset"
    assert bound["dtype_coverage"] == "role_aggregate"
    assert bound["full_tensor_headers"] is False
    assert bound["shaped_tensor_count"] > 0
    assert bound["shaped_tensor_count"] < bound["weight_tensor_count"]
    assert bound["source_url"] == document["source"]["url"]
    assert bound["weight_payload_bytes_read"] == 0
    assert bound["remote_connect"] is False
    assert _tensor(bound, "self_attn.q_a_proj.weight")["stored_dtype"] == "F8_E4M3"
    assert _tensor(bound, "self_attn.q_b_proj.weight")["stored_dtype"] == "F8_E4M3"
    assert _tensor(bound, "self_attn.kv_a_proj_with_mqa.weight")["stored_dtype"] == "F8_E4M3"
    assert _tensor(bound, "self_attn.kv_b_proj.weight")["stored_dtype"] == "BF16"
    assert _tensor(bound, "mlp.experts.0.up_proj.weight")["stored_dtype"] == "U8"
    assert _tensor(bound, "mlp.experts.0.up_proj.weight")["packed"] is True
    assert _tensor(bound, "mlp.shared_experts.up_proj.weight")["stored_dtype"] == "F8_E4M3"
    assert _tensor(bound, "mlp.shared_experts.up_proj.weight")["packed"] is False
    assert _tensor(bound, "mlp.experts.0.gate_proj.weight")["stored_dtype"] == "U8"
    assert _tensor(bound, "mlp.gate.weight")["stored_dtype"] == "BF16"
    assert _tensor(bound, "input_layernorm.weight")["stored_dtype"] == "F32"
    assert _tensor(bound, "input_layernorm.weight")["element_bytes"] == 4
    assert _tensor(bound, "input_layernorm.weight")["coverage"] == "shaped_subset"
    assert _tensor(bound, "self_attn.indexer.k_norm.weight")["stored_dtype"] == "F32"
    assert _tensor(bound, "self_attn.indexer.wk.weight")["stored_dtype"] == "BF16"
    assert _module(bound, "model.norm")["stored_dtype"] == "F32"
    assert _module(bound, "model.norm")["physical_bytes"] is None
    assert _module(bound, "model.norm")["byte_status"] == "category_count_is_not_bytes"
    assert _module(bound, "model.embed_tokens")["stored_dtype"] == "BF16"
    assert _module(bound, "model.layers.input_layernorm")["physical_bytes"] is None
    plain = quant.load_deployed_module_quant(GLM51_W4)
    assert plain["status"] == "mapped"
    assert plain["weight_counts"] == {"W4": 58368, "W8": 632, "FLOAT": 717}
    assert plain["header_binding"]["origin"] == "absent"
    assert plain["weight_stored_counts"] is None
    lied = json.loads(json.dumps(document))
    lied["identity"]["quant_sha256"] = "ab" * 32
    named = tmp_path / row["quant_sha256"]
    quant.write_header_provenance(named, lied)
    rejected = quant.load_deployed_module_quant(GLM51_W4, header_source=named)
    assert rejected["status"] == "ineligible"
    assert rejected["header_binding"]["reason"] == "metadata_mismatch"
    assert rejected["header_binding"]["source_eligible"] is False
    assert rejected["weight_stored_counts"] is None
    assert rejected["header_tensors"] == []
    assert quant.project_weight_work_units(rejected)["weight_counts"] is None


def test_failed_provenance_write_keeps_the_previous_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    quant = _load()
    document = quant.provenance_from_review_row(_archive_row("GLM-5.1-w4a4c8-mxfp4"))
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
    document = quant.provenance_from_review_row(_archive_row("GLM-5.1-w4a4c8-mxfp4"))
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


def test_replacement_loop_keeps_distinct_records_under_active_memory() -> None:
    quant = _load()
    observed = []
    for directory in (GLM51_W4, GLM53_W8, GLM51_W4):
        bound = quant.bind_deployed_weight_units(directory, header_archive=ARCHIVE)
        gate = _tensor(bound, "mlp.experts.0.gate_proj.weight")
        observed.append((
            directory.name,
            bound["description_sha256"],
            gate["stored_dtype"],
            gate["physical_bytes"],
            bound["weight_counts"]["W4"],
            bound["coverage"],
            bound["full_tensor_headers"],
        ))
    assert observed[0][0] == observed[2][0]
    assert observed[0][1] == observed[2][1]
    assert observed[0][1] != observed[1][1]
    assert observed[0][2] == "U8"
    assert observed[0][3] == 2048 * 3072
    assert observed[1][2] == "F8_E4M3"
    assert observed[1][3] == 2048 * 6144
    assert observed[1][4] == 0
    assert observed[2][2] == "U8"
    assert observed[2][3] == observed[0][3]
    assert observed[2][4] == 58368
    assert observed[0][5] == "role_aggregate_and_shaped_subset"
    assert observed[0][6] is False
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_bytes = rss if sys.platform == "darwin" else rss * 1024
    assert rss_bytes < 512 * 1024 * 1024
