"""Deployed per-module weight quantization from one checkpoint directory.

[Role]
  Read quant_model_description.json and the small config beside it.
  When the directory contains safetensors shards, read only each shard header.
  Otherwise bind stored dtype from a caller-declared header source whose
  directory name and config, description, and index hashes match.
  header_provenance.json in the same directory is optional and is not a default
  path. A mismatch there does not drop the scheme map.
  B consumes load_deployed_module_quant and bind_deployed_weight_units.

[Invariants]
  The directory is the selector. A config sha256 is recorded and is never a
  lookup key. Scale tensors are not counted as weights. Config dtype is not a
  substitute for a missing description. FLOAT is not a stored dtype. A category
  count is not a byte count. Shard tensor payloads are not read. No network.

[Timeouts & Locks]
  Local metadata reads. No device, no subprocess, no lock.

[Side-Effect Policy]
  Read-only. No cache written back into the checkpoint.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

import importlib.util
import sys

def _load_header_unit():
    try:
        from . import fleet_weight_headers as module
        return module
    except ImportError:
        pass
    name = "fleet_weight_headers"
    cached = sys.modules.get(name)
    if cached is not None and getattr(cached, "PROVENANCE_SCHEMA", None):
        return cached
    path = Path(__file__).resolve().with_name("fleet_weight_headers.py")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_HEADERS = _load_header_unit()
_binding = _HEADERS.binding
select_header_source = _HEADERS.select_header_source
select_archive = _HEADERS.select_archive
bind_local_headers = _HEADERS.bind_local_headers
prepare_modules = _HEADERS.prepare_modules
unit_status = _HEADERS.unit_status
_role = _HEADERS.role
_category = _HEADERS.category
layer_expert = _HEADERS.layer_expert
HEADER_ORIGINS = _HEADERS.HEADER_ORIGINS
PROVENANCE_SCHEMA = _HEADERS.PROVENANCE_SCHEMA
PROVENANCE_NAME = _HEADERS.PROVENANCE_NAME
write_header_provenance = _HEADERS.write_header_provenance
provenance_from_review_row = _HEADERS.provenance_from_review_row


SCHEMA = "fleet-weight-quantization/1"
_CONFIG_BUDGET = 1024 * 1024
_STREAM_LIMIT = 50 * 1024 * 1024
_READ_CHUNK = 1 << 20
_LAYER_LIST_LIMIT = 24
_WEIGHT_BUCKETS = {
    "W4A4_MXFP4": "W4",
    "W8A8_MXFP8": "W8",
    "FLOAT": "FLOAT",
}


def load_deployed_module_quant(
    weights_dir: str | Path,
    header_archive: str | Path | None = None,
    *,
    header_source: str | Path | None = None,
) -> dict[str, Any]:
    """Map one deployed sidecar. Missing description is not a guessed FLOAT model.

    header_source, or header_archive, is a file the caller declares. There is
    no default path and no remote connection. Local shard headers win when
    those files are present. A sibling header_provenance.json is tried only
    when both arguments are omitted, and only a matching file is applied.
    """
    root = Path(weights_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)
    declared = header_source if header_source is not None else header_archive
    optional = False
    if declared is None:
        sibling = root / PROVENANCE_NAME
        if sibling.is_file():
            declared = sibling
            optional = True
    description_path = root / "quant_model_description.json"
    config_path = root / "config.json"
    index_path = root / "quant_model_weights.safetensors.index.json"
    config_record, config = _read_config(config_path)
    shard_names = sorted(item.name for item in root.glob("*.safetensors") if item.is_file())
    index_record, weight_map = _read_index_record(index_path, shard_names, parse_map=bool(shard_names))
    architecture = _architecture(config_record, config)
    if not description_path.is_file():
        binding = _binding(
            source_eligible=False,
            reason="description_absent",
            local_shards=bool(shard_names),
            archive_path=str(declared) if declared is not None else None,
        )
        return _record(
            status="description_absent",
            root=root,
            sources={
                "quant_model_description": _absent(description_path),
                "config": config_record,
                "weight_index": index_record,
            },
            header={},
            architecture=architecture,
            weight_counts=None,
            parameter_counts={},
            modules=[],
            config=config,
            index_record=index_record,
            binding=binding,
            tensors=[],
            stored_counts=None,
            unknowns=[
                "quant_model_description.json absent; config dtype is not a per-tensor map",
            ],
        )
    raw, description_record = _read_description(description_path)
    header, groups = _accumulate(raw)
    modules = _modules(groups)
    prepare_modules(modules)
    parameter_counts = _parameter_counts(modules)
    weight_counts = _weight_counts(parameter_counts.get("weight") or {})
    if declared is not None and not Path(declared).is_file():
        raise FileNotFoundError(declared)
    local = bind_local_headers(root, raw, weight_map) if shard_names else None
    archive_row = None
    archive_reason = None
    rejected_model = None
    optional_failed = False
    if declared is not None and not (local and local["ok"]):
        try:
            archive_row, archive_reason, rejected_model = select_archive(
                declared,
                root.name,
                config_record.get("sha256"),
                description_record.get("sha256"),
                index_record.get("sha256"),
            )
        except (OSError, ValueError):
            if not optional:
                raise
            optional_failed = True
            declared = None
    binding, tensors, stored_counts, status = select_header_source(
        shard_names=shard_names,
        description=raw,
        modules=modules,
        local=local,
        archive_row=archive_row,
        archive_reason=archive_reason,
        rejected_model=rejected_model,
        header_archive=declared,
    )
    if optional and (optional_failed or status == "ineligible"):
        prepare_modules(modules)
        tensors = []
        stored_counts = None
        status = "mapped"
        binding = _binding(
            source_eligible=True,
            reason="no_header_source",
            flag="optional_provenance_not_applied",
            local_shards=bool(shard_names),
            archive_path=str(root / PROVENANCE_NAME),
        )
    elif status == "ineligible":
        prepare_modules(modules)
        stored_counts = None
        tensors = []
    return _record(
        status=status,
        root=root,
        sources={
            "quant_model_description": description_record,
            "config": config_record,
            "weight_index": index_record,
        },
        header=header,
        architecture=architecture,
        weight_counts=weight_counts,
        parameter_counts=parameter_counts,
        modules=modules,
        config=config,
        index_record=index_record,
        binding=binding,
        tensors=tensors,
        stored_counts=stored_counts,
        unknowns=list(_unknowns(header, config, index_record, binding)),
    )


def bind_deployed_weight_units(
    weights_dir: str | Path,
    header_archive: str | Path | None = None,
    *,
    header_source: str | Path | None = None,
) -> dict[str, Any]:
    """End-to-end binding B prices. FLOAT is not rewritten to BF16."""
    return project_weight_work_units(
        load_deployed_module_quant(
            weights_dir,
            header_archive=header_archive,
            header_source=header_source,
        )
    )


def project_weight_work_units(record: Mapping[str, Any]) -> dict[str, Any]:
    """Project a loader record. Ineligible archives contribute no dtype and no bytes."""
    binding = record.get("header_binding") if isinstance(record.get("header_binding"), Mapping) else {}
    sources = record.get("sources") if isinstance(record.get("sources"), Mapping) else {}
    description = sources.get("quant_model_description") if isinstance(sources.get("quant_model_description"), Mapping) else {}
    index = sources.get("weight_index") if isinstance(sources.get("weight_index"), Mapping) else {}
    architecture = record.get("architecture") if isinstance(record.get("architecture"), Mapping) else {}
    status = record.get("status")
    origin = binding.get("origin")
    stored_dtype_bound = status == "mapped" and binding.get("source_eligible") is True and origin in HEADER_ORIGINS
    base = {
        "schema": SCHEMA,
        "status": status,
        "source_eligible": bool(stored_dtype_bound or (status == "mapped" and binding.get("source_eligible") is True)),
        "stored_dtype_bound": stored_dtype_bound,
        "reason": binding.get("reason"),
        "origin": origin,
        "flag": binding.get("flag"),
        "remote_connect": False,
        "manifest_sha256": binding.get("manifest_sha256"),
        "config_sha256": architecture.get("config_sha256"),
        "description_sha256": description.get("sha256"),
        "index_sha256": index.get("sha256"),
        "index_total_size_bytes": index.get("total_size_bytes"),
        "weight_payload_bytes_read": 0,
        "coverage": binding.get("coverage"),
        "layer_coverage": binding.get("layer_coverage"),
        "dtype_coverage": binding.get("dtype_coverage"),
        "full_tensor_headers": binding.get("full_tensor_headers"),
        "shaped_tensor_count": binding.get("shaped_tensor_count"),
        "weight_tensor_count": binding.get("weight_tensor_count"),
        "source_url": binding.get("source_url"),
    }
    if status != "mapped":
        return {
            **base,
            "source_eligible": False,
            "stored_dtype_bound": False,
            "weight_counts": None,
            "weight_stored_counts": None,
            "modules": [],
            "tensors": [],
        }
    modules = []
    for row in record.get("modules") or []:
        if not isinstance(row, Mapping) or row.get("role") != "weight":
            continue
        modules.append({
            "category": row.get("category"),
            "scheme": row.get("scheme"),
            "stored_dtype": row.get("stored_dtype") if stored_dtype_bound else None,
            "count": row.get("count"),
            "physical_bytes": row.get("physical_bytes") if stored_dtype_bound else None,
            "logical_elements": row.get("logical_elements") if stored_dtype_bound else None,
            "byte_status": row.get("byte_status"),
        })
    units = record.get("units") if isinstance(record.get("units"), Mapping) else {}
    return {
        **base,
        "weight_counts": record.get("weight_counts"),
        "weight_stored_counts": record.get("weight_stored_counts") if stored_dtype_bound else None,
        "modules": modules,
        "tensors": list(record.get("header_tensors") or []) if stored_dtype_bound else [],
        "weight_payload_bytes_read": units.get("weight_payload_bytes_read", 0),
    }


def _record(
    *,
    status: str,
    root: Path,
    sources: dict[str, Any],
    header: Mapping[str, Any],
    architecture: dict[str, Any],
    weight_counts: dict[str, int] | None,
    parameter_counts: Mapping[str, Any],
    modules: list[dict[str, Any]],
    config: Mapping[str, Any],
    index_record: Mapping[str, Any],
    binding: dict[str, Any],
    tensors: list[dict[str, Any]],
    stored_counts: dict[str, int] | None,
    unknowns: list[str],
) -> dict[str, Any]:
    per_tensor_status, reason = unit_status(index_record, binding, tensors)
    return {
        "schema": SCHEMA,
        "status": status,
        "weights_dir": str(root),
        "sources": sources,
        "header": dict(header),
        "architecture": architecture,
        "weight_counts": weight_counts,
        "weight_stored_counts": stored_counts,
        "parameter_counts": dict(parameter_counts),
        "modules": modules,
        "header_binding": binding,
        "header_tensors": tensors,
        "kv": _kv(modules, config),
        "mtp": _mtp(modules, config),
        "units": _units(index_record, header_bytes_read=int(binding.get("header_bytes_read") or 0), per_tensor_status=per_tensor_status, reason=reason),
        "unknowns": unknowns,
    }


def _read_description(path: Path) -> tuple[Mapping[str, Any], dict[str, Any]]:
    document, digest, size, mode = _read_json_object(path)
    if not isinstance(document, dict):
        raise ValueError(f"{path} is not a JSON object")
    return document, {
        "path": str(path),
        "sha256": digest,
        "bytes": size,
        "present": True,
        "read_mode": mode,
    }


def _read_json_object(path: Path) -> tuple[Any, str, int, str]:
    """Files at most 50 MiB use one size-bounded read. Larger files use 1 MiB chunks.

    A valid large JSON object is accepted. The object is one value, so the
    parser sees the bytes after the chunked read. The read itself is bounded.
    """
    size = path.stat().st_size
    digest = hashlib.sha256()
    if size <= _STREAM_LIMIT:
        with path.open("rb") as handle:
            payload = handle.read(size)
        if len(payload) != size:
            raise ValueError(f"{path} changed while reading")
        digest.update(payload)
        document = json.loads(payload)
        return document, digest.hexdigest(), size, "bounded"
    parts: list[bytes] = []
    with path.open("rb") as handle:
        while True:
            block = handle.read(_READ_CHUNK)
            if not block:
                break
            digest.update(block)
            parts.append(block)
    payload = b"".join(parts)
    text = payload.decode("utf-8")
    document, end = json.JSONDecoder().raw_decode(text)
    if text[end:].strip():
        raise ValueError(f"{path} has trailing data after the JSON value")
    return document, digest.hexdigest(), size, "stream"


def _read_config(path: Path) -> tuple[dict[str, Any], Mapping[str, Any]]:
    if not path.is_file():
        return _absent(path), {}
    size = path.stat().st_size
    record = {
        "path": str(path),
        "sha256": _sha256(path),
        "bytes": size,
        "present": True,
    }
    if size > _CONFIG_BUDGET:
        record["skipped"] = "over_1mib"
        return record, {}
    with path.open("rb") as handle:
        payload = handle.read(size)
    if len(payload) != size:
        raise ValueError(f"{path} changed while reading")
    document = json.loads(payload)
    if not isinstance(document, dict):
        return record, {}
    return record, document


def _read_index_record(path: Path, shard_names: list[str], *, parse_map: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    record: dict[str, Any] = {
        "path": str(path),
        "present": path.is_file(),
        "shards_present": bool(shard_names),
        "shard_names": list(shard_names),
        "total_size_bytes": None,
        "sha256": None,
        "bytes": None,
    }
    if not path.is_file():
        return record, {}
    if not parse_map:
        record["sha256"] = _sha256(path)
        record["bytes"] = path.stat().st_size
        with path.open("rb") as handle:
            prefix = handle.read(4096)
        matched = re_total_size(prefix)
        if matched is not None:
            record["total_size_bytes"] = matched
        return record, {}
    document, digest, size, mode = _read_json_object(path)
    record["sha256"] = digest
    record["bytes"] = size
    record["read_mode"] = mode
    weight_map: dict[str, Any] = {}
    if isinstance(document, dict):
        total = _total_size_field(document)
        if total is not None:
            record["total_size_bytes"] = total
        raw_map = document.get("weight_map")
        if isinstance(raw_map, dict):
            weight_map = raw_map
    return record, weight_map


def re_total_size(prefix: bytes) -> int | None:
    matched = re.search(br'"total_size"\s*:\s*(\d+)', prefix)
    if matched is None:
        return None
    return int(matched.group(1))


def _total_size_field(document: Mapping[str, Any]) -> int | None:
    total = document.get("total_size")
    if isinstance(total, int) and not isinstance(total, bool):
        return total
    metadata = document.get("metadata")
    if isinstance(metadata, Mapping):
        nested = metadata.get("total_size")
        if isinstance(nested, int) and not isinstance(nested, bool):
            return nested
    return None


def _absent(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": None, "bytes": None, "present": False}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(_READ_CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _architecture(config_record: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    architectures = config.get("architectures")
    return {
        "config_sha256": config_record.get("sha256"),
        "model_type": config.get("model_type"),
        "architectures": list(architectures) if isinstance(architectures, list) else None,
        "num_hidden_layers": config.get("num_hidden_layers") if isinstance(config.get("num_hidden_layers"), int) else None,
        "dtype": config.get("dtype") if isinstance(config.get("dtype"), str) else None,
        "selects_weights": False,
    }


def _accumulate(document: Mapping[str, Any]) -> tuple[dict[str, Any], dict[tuple[str, str, str], dict[str, Any]]]:
    header: dict[str, Any] = {}
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for key, value in document.items():
        if "." not in key:
            header[key] = value
            continue
        if not isinstance(value, str):
            continue
        item_role = _role(key)
        item_category = _category(key, item_role)
        bucket = _WEIGHT_BUCKETS.get(value, value)
        slot = groups.get((item_category, item_role, value))
        if slot is None:
            slot = {
                "category": item_category,
                "role": item_role,
                "scheme": value,
                "bucket": bucket,
                "count": 0,
                "layers": set(),
                "sample_key": key,
            }
            groups[(item_category, item_role, value)] = slot
        slot["count"] += 1
        layer, _expert = layer_expert(key)
        if layer is not None:
            slot["layers"].add(layer)
    return header, groups


def _modules(groups: Mapping[tuple[str, str, str], Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for slot in groups.values():
        layers = sorted(slot["layers"])
        row = {
            "category": slot["category"],
            "role": slot["role"],
            "scheme": slot["scheme"],
            "bucket": slot["bucket"],
            "count": slot["count"],
            "layer_count": len(layers),
            "sample_key": slot["sample_key"],
        }
        if layers and len(layers) <= _LAYER_LIST_LIMIT:
            row["layers"] = layers
        rows.append(row)
    rows.sort(key=lambda item: (item["category"], item["role"], item["scheme"]))
    return rows


def _parameter_counts(modules: list[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in modules:
        role_counts = counts.setdefault(str(row["role"]), {})
        scheme = str(row["scheme"])
        role_counts[scheme] = role_counts.get(scheme, 0) + int(row["count"])
    return counts


def _weight_counts(weight_schemes: Mapping[str, int]) -> dict[str, int]:
    counts = {"W4": 0, "W8": 0, "FLOAT": 0}
    for scheme, count in weight_schemes.items():
        bucket = _WEIGHT_BUCKETS.get(scheme, scheme)
        counts[bucket] = counts.get(bucket, 0) + int(count)
    return counts


def _kv(modules: list[Mapping[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    attention = [row for row in modules if row["category"] == "model.layers.self_attn" and row["role"] == "declaration"]
    projections = [
        row for row in modules
        if row["role"] == "weight" and (".kv_a" in str(row["category"]) or ".kv_b" in str(row["category"]))
    ]
    cache_field = None
    for name in ("kv_cache_dtype", "kv_quant", "kv_cache_quant"):
        if name in config:
            cache_field = name
            break
    return {
        "cache_quant": config.get(cache_field) if cache_field else None,
        "cache_quant_status": "declared" if cache_field else "unknown",
        "cache_quant_field": cache_field,
        "kv_lora_rank": config.get("kv_lora_rank") if isinstance(config.get("kv_lora_rank"), int) else None,
        "attention_quant_type": [
            {"scheme": row["scheme"], "count": row["count"], "layer_count": row["layer_count"]}
            for row in attention
        ],
        "projection_modules": [
            {"category": row["category"], "scheme": row["scheme"], "count": row["count"]}
            for row in projections
        ],
        "provenance": [
            "config.json fields kv_cache_dtype, kv_quant, kv_cache_quant when present",
            "quant_model_description self_attn.quant_type is left on the attention module",
            "kv_a and kv_b weight labels are projection storage, not a cache dtype",
        ],
    }


def _mtp(modules: list[Mapping[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    markers = ("eh_proj", "enorm", "hnorm", "shared_head", "model.layers.embed_tokens")
    selected = [
        row for row in modules
        if row["role"] == "weight" and any(marker in str(row["category"]) for marker in markers)
    ]
    share = config.get("index_share_for_mtp_iteration") if "index_share_for_mtp_iteration" in config else None
    layers = config.get("num_nextn_predict_layers")
    return {
        "num_nextn_predict_layers": layers if isinstance(layers, int) else None,
        "index_share_for_mtp_iteration": share if isinstance(share, bool) else None,
        "modules": [
            {
                "category": row["category"],
                "scheme": row["scheme"],
                "count": row["count"],
                "layers": row.get("layers"),
            }
            for row in selected
        ],
        "provenance": [
            "config.json num_nextn_predict_layers",
            "config.json index_share_for_mtp_iteration when the key exists",
            "description keys eh_proj, enorm, hnorm, shared_head, model.layers.embed_tokens",
        ],
    }


def _units(index_record: Mapping[str, Any], *, header_bytes_read: int, per_tensor_status: str, reason: str) -> dict[str, Any]:
    return {
        "per_tensor_status": per_tensor_status,
        "reason": reason,
        "index_total_size_bytes": index_record.get("total_size_bytes"),
        "weight_payload_bytes_read": 0,
        "header_bytes_read": header_bytes_read,
    }


def _unknowns(header: Mapping[str, Any], config: Mapping[str, Any], index_record: Mapping[str, Any], binding: Mapping[str, Any]) -> list[str]:
    notes = []
    if binding.get("origin") not in HEADER_ORIGINS and not index_record.get("shards_present"):
        notes.append("per_tensor_shape_unknown")
    if binding.get("flag"):
        notes.append(str(binding["flag"]))
    if "kv_cache_dtype" not in config and "kv_quant" not in config and "kv_cache_quant" not in config:
        notes.append("kv_cache_quant_unknown")
    indexer = header.get("indexer_quant_type")
    if isinstance(indexer, str):
        notes.append(f"header_indexer_quant_type:{indexer}")
    return notes
