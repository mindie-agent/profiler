"""Read safetensors headers and declared header provenance. No tensor payload.

[Role]
  Bind stored dtype and measured sizes for one deployment directory.
  Local shard headers are the complete source when those files are present.
  A caller-declared provenance file, or header_provenance.json in that same
  directory, supplies role aggregates and whatever shaped tensors it actually
  stores. A review receipt is not a default path.

[Invariants]
  Payloads are not read. No device and no network. FLOAT is not a width.
  Category counts are not bytes. A shaped subset is not layer-complete coverage.
  Identity is the config, description, and index sha256 triple inside the file.
  The file name is not a hash. No module-level cache.

[Timeouts & Locks]
  Chunked local reads. No lock. One directory is active per call.

[Side-Effect Policy]
  Reads are read-only. write_header_provenance replaces a file only after the
  new body is complete. A failed write leaves the previous file in place.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Any, Mapping

PROVENANCE_SCHEMA = "fleet-weight-header-provenance/1"
PROVENANCE_NAME = "header_provenance.json"
HEADER_ORIGINS = {"local_shard_header", "acquired_header_archive"}
_STREAM_LIMIT = 50 * 1024 * 1024
_READ_CHUNK = 1 << 20
_HEADER_MAX = 50_000_000
_ELEMENT_BYTES = {
    "BOOL": 1,
    "U8": 1,
    "I8": 1,
    "F8_E4M3": 1,
    "F8_E5M2": 1,
    "F16": 2,
    "BF16": 2,
    "I16": 2,
    "U16": 2,
    "F32": 4,
    "I32": 4,
    "U32": 4,
    "F64": 8,
    "I64": 8,
    "U64": 8,
}
_PACKED_U8_SCHEMES = {"W4A4_MXFP4": 2, "W4A8_MXFP": 2}
_INDEXED_TOKENS = {"layers", "experts", "blocks"}
_LAYER_RE_TOKENS = ("layers", "experts")
_INELIGIBLE_REASONS = {
    "metadata_mismatch",
    "identity_name_mismatch",
    "ambiguous_archive_match",
    "archive_lacks_header_manifest",
    "local_header_incomplete",
}
_HEX = set("0123456789abcdef")


def binding(**kwargs: Any) -> dict[str, Any]:
    base = {
        "origin": "absent",
        "source_eligible": False,
        "reason": "no_header_source",
        "manifest_sha256": None,
        "acquired_host": None,
        "source_url": None,
        "local_shards": False,
        "metadata_matches_archive": None,
        "full_tensor_headers": False,
        "coverage": "none",
        "layer_coverage": "absent",
        "dtype_coverage": "absent",
        "shaped_tensor_count": 0,
        "weight_tensor_count": None,
        "remote_connect": False,
        "flag": None,
        "header_bytes_read": 0,
        "acquired_header_bytes": None,
        "archive_path": None,
        "rejected_archive_model": None,
        "shard_reads": [],
    }
    base.update(kwargs)
    base["remote_connect"] = False
    return base


def select_header_source(
    *,
    shard_names: list[str],
    description: Mapping[str, Any],
    modules: list[dict[str, Any]],
    local: Mapping[str, Any] | None,
    archive_row: Mapping[str, Any] | None,
    archive_reason: str | None,
    rejected_model: str | None,
    header_archive: str | Path | None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int] | None, str]:
    archive_path = str(header_archive) if header_archive is not None else None
    weight_keys = weight_key_count(description)
    if local and local.get("ok"):
        apply_measured_modules(modules, local["tensors"])
        stored = counts_from_tensors(local["tensors"])
        full = bool(local.get("full"))
        record = binding(
            origin="local_shard_header",
            source_eligible=True,
            reason="local_shard_header",
            manifest_sha256=local.get("manifest_sha256"),
            local_shards=True,
            metadata_matches_archive=True if archive_row is not None else None,
            full_tensor_headers=full,
            coverage="shard_headers",
            layer_coverage="complete" if full else "subset",
            dtype_coverage="per_tensor",
            shaped_tensor_count=len(local["tensors"]),
            weight_tensor_count=weight_keys,
            header_bytes_read=int(local.get("header_bytes") or 0),
            archive_path=archive_path,
            shard_reads=list(local.get("shard_reads") or []),
        )
        return record, list(local["tensors"]), stored, "mapped"
    if archive_row is not None:
        tensors = archive_tensors(archive_row.get("layer3_modules"), description)
        apply_archive_roles(modules, archive_row.get("module_types"))
        stored = counts_from_groups(archive_row.get("native_declared_groups"))
        claims_full = archive_row.get("full_tensor_headers") is True and archive_row.get("coverage") == "shard_headers"
        full = bool(claims_full and weight_keys > 0 and len(tensors) == weight_keys)
        flag = None if full else "archive_lacks_tensor_headers_metadata_matches"
        acquired = archive_row.get("header_bytes_read")
        coverage = "shard_headers" if full else "role_aggregate_and_shaped_subset"
        record = binding(
            origin="acquired_header_archive",
            source_eligible=True,
            reason="acquired_header_archive",
            manifest_sha256=archive_row.get("header_manifest_sha256"),
            acquired_host=archive_row.get("host") if isinstance(archive_row.get("host"), str) else None,
            source_url=archive_row.get("source_url") if isinstance(archive_row.get("source_url"), str) else None,
            local_shards=bool(shard_names),
            metadata_matches_archive=True,
            full_tensor_headers=full,
            coverage=coverage,
            layer_coverage="complete" if full else "subset",
            dtype_coverage="per_tensor" if full else "role_aggregate",
            shaped_tensor_count=len(tensors),
            weight_tensor_count=weight_keys,
            flag=flag,
            acquired_header_bytes=acquired if isinstance(acquired, int) and not isinstance(acquired, bool) else None,
            archive_path=archive_path,
        )
        return record, tensors, stored, "mapped"
    if local and not local.get("ok"):
        record = binding(
            source_eligible=False,
            reason="local_header_incomplete",
            local_shards=True,
            metadata_matches_archive=False if archive_reason else None,
            weight_tensor_count=weight_keys,
            archive_path=archive_path,
            rejected_archive_model=rejected_model,
        )
        return record, [], None, "ineligible"
    if archive_reason in _INELIGIBLE_REASONS:
        record = binding(
            source_eligible=False,
            reason=archive_reason,
            local_shards=bool(shard_names),
            metadata_matches_archive=False,
            weight_tensor_count=weight_keys,
            archive_path=archive_path,
            rejected_archive_model=rejected_model,
        )
        return record, [], None, "ineligible"
    record = binding(
        source_eligible=True,
        reason="no_header_source",
        local_shards=bool(shard_names),
        weight_tensor_count=weight_keys,
        archive_path=archive_path,
    )
    return record, [], None, "mapped"


def select_archive(
    header_archive: str | Path,
    directory: str,
    config_sha: Any,
    quant_sha: Any,
    index_sha: Any,
) -> tuple[Mapping[str, Any] | None, str | None, str | None]:
    path = Path(header_archive)
    if not path.is_file():
        raise FileNotFoundError(path)
    rows = read_header_rows(path)
    wanted = (config_sha, quant_sha, index_sha)
    wanted_ok = all(_hex64(item) for item in wanted)
    header_rows = [row for row in rows if _hex64(row.get("cfg_sha256"))]
    name_rows = [row for row in header_rows if row.get("model") == directory]
    hash_rows = [row for row in header_rows if wanted_ok and _row_hashes(row) == wanted]
    exact = [
        row for row in hash_rows
        if row.get("model") == directory and _hex64(row.get("header_manifest_sha256"))
    ]
    if len(exact) == 1:
        return exact[0], None, None
    if len(exact) > 1:
        return None, "ambiguous_archive_match", None
    if any(_row_hashes(row) == wanted and wanted_ok for row in name_rows):
        return None, "archive_lacks_header_manifest", None
    if name_rows:
        return None, "metadata_mismatch", None
    if hash_rows:
        names = {str(row.get("model")) for row in hash_rows if isinstance(row.get("model"), str)}
        if len(names) == 1:
            return None, "identity_name_mismatch", next(iter(names))
        return None, "ambiguous_archive_match", None
    return None, "metadata_mismatch", None


def read_header_rows(path: Path) -> list[dict[str, Any]]:
    payload = _chunked_bytes(path)
    text = payload.decode("utf-8")
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            document = None
        if isinstance(document, dict):
            return [_normalize_row(document)]
    rows = []
    for line in text.splitlines():
        if line.strip():
            document = json.loads(line)
            if not isinstance(document, dict):
                raise ValueError(f"{path} archive row is not a JSON object")
            rows.append(_normalize_row(document))
    return rows


def bind_local_headers(root: Path, description: Mapping[str, Any], weight_map: Mapping[str, Any]) -> dict[str, Any]:
    by_shard: dict[str, list[tuple[str, str]]] = {}
    missing_index: list[str] = []
    for key, scheme in description.items():
        if not isinstance(key, str) or not key.endswith(".weight") or not isinstance(scheme, str):
            continue
        shard = weight_map.get(key)
        if not isinstance(shard, str):
            missing_index.append(key)
            continue
        by_shard.setdefault(shard, []).append((key, scheme))
    manifest = hashlib.sha256()
    tensors: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    shard_reads: list[dict[str, Any]] = []
    header_bytes = 0
    for shard_name, items in sorted(by_shard.items()):
        shard_path = root / shard_name
        if not shard_path.is_file():
            errors.append({"shard": shard_name, "error": "missing"})
            continue
        try:
            document, raw, size = read_safetensor_header(shard_path)
        except (OSError, ValueError) as exc:
            errors.append({"shard": shard_name, "error": type(exc).__name__})
            continue
        header_bytes += size
        manifest.update(shard_name.encode() + b"\0" + hashlib.sha256(raw).digest())
        shard_reads.append({
            "name": shard_name,
            "header_bytes": size,
            "prefix_bytes": 8,
            "file_bytes": shard_path.stat().st_size,
            "payload_bytes_read": 0,
        })
        for key, scheme in items:
            meta = document.get(key)
            if not isinstance(meta, Mapping) or not isinstance(meta.get("dtype"), str) or "shape" not in meta:
                errors.append({"shard": shard_name, "key": key, "error": "header_key_missing"})
                continue
            measured = measure(scheme, meta["dtype"], meta.get("shape"))
            if measured is None:
                errors.append({"shard": shard_name, "key": key, "error": "shape_rejected"})
                continue
            layer, expert = layer_expert(key)
            tensors.append(_tensor_row(key, scheme, measured, layer, expert, shard_name, "per_tensor"))
    tensors.sort(key=lambda item: item["key"])
    expected = sum(len(items) for items in by_shard.values())
    ok = not errors and not missing_index and expected > 0 and len(tensors) == expected
    return {
        "ok": ok,
        "full": ok,
        "tensors": tensors if ok else [],
        "header_bytes": header_bytes if ok else 0,
        "manifest_sha256": manifest.hexdigest() if ok else None,
        "shard_reads": shard_reads if ok else [],
        "errors": errors,
        "missing_index": missing_index,
    }


def read_safetensor_header(path: Path) -> tuple[dict[str, Any], bytes, int]:
    """Read the uint64 length and that many header bytes. Do not read data_offsets."""
    with path.open("rb") as handle:
        prefix = handle.read(8)
        if len(prefix) != 8:
            raise ValueError(f"{path} is shorter than a safetensors header")
        size = struct.unpack("<Q", prefix)[0]
        if size < 2 or size >= _HEADER_MAX:
            raise ValueError(f"{path} header length is not a safetensors header")
        raw = handle.read(size)
        if len(raw) != size:
            raise ValueError(f"{path} header is truncated")
    document = json.loads(raw)
    if not isinstance(document, dict):
        raise ValueError(f"{path} header is not a JSON object")
    return document, raw, size


def provenance_from_review_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Copy one review row into the stable provenance schema.

    Shaped tensors in that row stay a subset. Aggregate group counts stay counts.
    The url is the receipt read root file:///mnt/weight/<directory> on the recorded host.
    """
    directory = row.get("model")
    host = row.get("host")
    if not isinstance(directory, str) or not directory or not isinstance(host, str) or not host:
        raise ValueError("review row has no directory and host")
    document = {
        "schema": PROVENANCE_SCHEMA,
        "source": {
            "host": host,
            "directory": directory,
            "url": f"file:///mnt/weight/{directory}",
            "read_root": "/mnt/weight",
        },
        "identity": {
            "config_sha256": row.get("cfg_sha256"),
            "quant_sha256": row.get("quant_sha256"),
            "index_sha256": row.get("index_sha256"),
        },
        "manifest_sha256": row.get("header_manifest_sha256"),
        "coverage": "role_aggregate_and_shaped_subset",
        "full_tensor_headers": False,
        "shaped_scope": "subset",
        "native_declared_groups": row.get("native_declared_groups") if isinstance(row.get("native_declared_groups"), dict) else {},
        "module_types": row.get("module_types") if isinstance(row.get("module_types"), dict) else {},
        "shaped_tensors": row.get("layer3_modules") if isinstance(row.get("layer3_modules"), dict) else {},
        "acquired_header_bytes": row.get("header_bytes_read") if isinstance(row.get("header_bytes_read"), int) else None,
    }
    validate_provenance(document)
    return document


def write_header_provenance(path: str | Path, document: Mapping[str, Any]) -> dict[str, Any]:
    """Write provenance atomically. The previous file remains if validation or the write fails."""
    validate_provenance(document)
    target = Path(path)
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict) or parsed.get("identity") != document.get("identity"):
        raise ValueError("provenance identity was not taken from the body")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".partial")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return {"path": str(target), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def validate_provenance(document: Mapping[str, Any]) -> None:
    if document.get("schema") != PROVENANCE_SCHEMA:
        raise ValueError("provenance schema is not fleet-weight-header-provenance/1")
    source = document.get("source")
    identity = document.get("identity")
    if not isinstance(source, Mapping) or not isinstance(identity, Mapping):
        raise ValueError("provenance source and identity are required")
    if not isinstance(source.get("host"), str) or not source.get("host"):
        raise ValueError("provenance host is required")
    if not isinstance(source.get("directory"), str) or not source.get("directory"):
        raise ValueError("provenance directory is required")
    url = source.get("url")
    if url is not None and not isinstance(url, str):
        raise ValueError("provenance url must be a string when present")
    for key in ("config_sha256", "quant_sha256", "index_sha256"):
        if not _hex64(identity.get(key)):
            raise ValueError(f"provenance {key} is not a sha256 body")
    if not _hex64(document.get("manifest_sha256")):
        raise ValueError("provenance manifest_sha256 is not a sha256 body")
    if document.get("coverage") not in {"role_aggregate_and_shaped_subset", "shard_headers"}:
        raise ValueError("provenance coverage is not a supported value")
    if document.get("full_tensor_headers") is True and document.get("coverage") != "shard_headers":
        raise ValueError("subset provenance cannot claim full tensor headers")
    if not isinstance(document.get("native_declared_groups"), Mapping):
        raise ValueError("provenance native_declared_groups is required")
    if not isinstance(document.get("module_types"), Mapping):
        raise ValueError("provenance module_types is required")
    if not isinstance(document.get("shaped_tensors"), Mapping):
        raise ValueError("provenance shaped_tensors is required")


def prepare_modules(modules: list[dict[str, Any]]) -> None:
    for row in modules:
        row["stored_dtype"] = None
        row["stored_header_count"] = None
        row["physical_bytes"] = None
        row["logical_elements"] = None
        row["dtype_coverage"] = "absent"
        row["layer_coverage"] = "absent"
        row["byte_status"] = "not_a_weight" if row.get("role") != "weight" else "no_header_source"


def unit_status(index_record: Mapping[str, Any], record: Mapping[str, Any], tensors: list[Mapping[str, Any]]) -> tuple[str, str]:
    del tensors
    origin = record.get("origin")
    if origin == "local_shard_header":
        return "measured", "safetensors headers were read; tensor payloads were not read"
    if origin == "acquired_header_archive":
        if record.get("full_tensor_headers") is True and record.get("layer_coverage") == "complete":
            return "measured", "declared header source stores a shape for every weight tensor"
        return "partial", "header source has role aggregates and only its shaped subset; category counts were not converted to bytes"
    if record.get("reason") in _INELIGIBLE_REASONS:
        return "rejected", str(record.get("reason"))
    if index_record.get("shards_present"):
        return "not_read", "shard headers were not requested"
    return "unknown", "safetensors shards named by the index are not in this directory; shape was not invented from config"


def role(key: str) -> str:
    tail = key.rsplit(".", 1)[-1]
    if tail == "weight_scale":
        return "scale"
    if tail == "weight":
        return "weight"
    if tail == "bias":
        return "bias"
    return "declaration"


def category(key: str, role_name: str) -> str:
    parts = [part for part in key.split(".") if not part.isdigit()]
    if role_name == "scale" and parts and parts[-1] == "weight_scale":
        parts = parts[:-1]
    elif role_name == "weight" and parts and parts[-1] == "weight":
        parts = parts[:-1]
    elif role_name == "bias" and parts and parts[-1] == "bias":
        parts = parts[:-1]
    elif role_name == "declaration" and parts and parts[-1] == "quant_type":
        parts = parts[:-1]
    return ".".join(parts)


def layer_expert(key: str) -> tuple[int | None, int | None]:
    layer = None
    expert = None
    parts = key.split(".")
    for index, part in enumerate(parts[:-1]):
        if part in _LAYER_RE_TOKENS and parts[index + 1].isdigit():
            if part == "layers":
                layer = int(parts[index + 1])
            else:
                expert = int(parts[index + 1])
    return layer, expert


def measure(scheme: str, dtype: str, shape: Any) -> dict[str, Any] | None:
    if not isinstance(shape, list) or any(isinstance(dim, bool) or not isinstance(dim, int) or dim < 0 for dim in shape):
        return None
    stored = 1
    for dim in shape:
        stored *= dim
    width = _ELEMENT_BYTES.get(dtype)
    packed_factor = _PACKED_U8_SCHEMES.get(scheme) if dtype == "U8" else None
    if width is None:
        return {
            "stored_dtype": dtype,
            "shape": list(shape),
            "stored_elements": stored,
            "element_bytes": None,
            "physical_bytes": None,
            "logical_elements": None,
            "packed": None,
        }
    if packed_factor:
        logical = stored * packed_factor
        packed = True
    else:
        logical = stored
        packed = False
    return {
        "stored_dtype": dtype,
        "shape": list(shape),
        "stored_elements": stored,
        "element_bytes": width,
        "physical_bytes": stored * width,
        "logical_elements": logical,
        "packed": packed,
    }


def _normalize_row(document: Mapping[str, Any]) -> dict[str, Any]:
    if document.get("schema") == PROVENANCE_SCHEMA:
        source = document.get("source") if isinstance(document.get("source"), Mapping) else {}
        identity = document.get("identity") if isinstance(document.get("identity"), Mapping) else {}
        coverage = document.get("coverage")
        claims_full = document.get("full_tensor_headers") is True and coverage == "shard_headers"
        return {
            "model": source.get("directory"),
            "host": source.get("host"),
            "source_url": source.get("url") if isinstance(source.get("url"), str) else None,
            "cfg_sha256": identity.get("config_sha256"),
            "quant_sha256": identity.get("quant_sha256"),
            "index_sha256": identity.get("index_sha256"),
            "header_manifest_sha256": document.get("manifest_sha256"),
            "native_declared_groups": document.get("native_declared_groups") or {},
            "module_types": document.get("module_types") or {},
            "layer3_modules": document.get("shaped_tensors") or {},
            "header_bytes_read": document.get("acquired_header_bytes"),
            "coverage": "shard_headers" if claims_full else "role_aggregate_and_shaped_subset",
            "full_tensor_headers": claims_full,
        }
    row = dict(document)
    row["coverage"] = "role_aggregate_and_shaped_subset"
    row["full_tensor_headers"] = False
    row["source_url"] = None
    return row


def _row_hashes(row: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    return (row.get("cfg_sha256"), row.get("quant_sha256"), row.get("index_sha256"))


def _hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in _HEX for char in value)


def _chunked_bytes(path: Path) -> bytes:
    parts: list[bytes] = []
    with path.open("rb") as handle:
        while True:
            block = handle.read(_READ_CHUNK)
            if not block:
                break
            parts.append(block)
    return b"".join(parts)


def archive_tensors(layer_rows: Any, description: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(layer_rows, Mapping):
        return []
    tensors = []
    for key, value in layer_rows.items():
        if not isinstance(key, str) or not isinstance(value, list) or len(value) < 4:
            continue
        if not isinstance(description.get(key), str):
            continue
        dtype = value[1]
        shape = value[2]
        shard = value[3]
        if not isinstance(dtype, str) or not isinstance(shard, str):
            continue
        measured = measure(description[key], dtype, shape)
        if measured is None:
            continue
        layer, expert = layer_expert(key)
        tensors.append(_tensor_row(key, description[key], measured, layer, expert, shard, "shaped_subset"))
    tensors.sort(key=lambda item: item["key"])
    return tensors


def _tensor_row(key: str, scheme: str, measured: Mapping[str, Any], layer: int | None, expert: int | None, shard: str, coverage: str) -> dict[str, Any]:
    return {
        "key": key,
        "category": category(key, "weight"),
        "role": "weight",
        "layer": layer,
        "expert": expert,
        "declared_scheme": scheme,
        "stored_dtype": measured["stored_dtype"],
        "shape": measured["shape"],
        "stored_elements": measured["stored_elements"],
        "element_bytes": measured["element_bytes"],
        "physical_bytes": measured["physical_bytes"],
        "logical_elements": measured["logical_elements"],
        "packed": measured["packed"],
        "shard": shard,
        "coverage": coverage,
    }


def apply_measured_modules(modules: list[dict[str, Any]], tensors: list[Mapping[str, Any]]) -> None:
    grouped: dict[tuple[Any, Any], list[Mapping[str, Any]]] = {}
    for tensor in tensors:
        grouped.setdefault((tensor.get("category"), tensor.get("declared_scheme")), []).append(tensor)
    for row in modules:
        if row.get("role") != "weight":
            continue
        members = grouped.get((row.get("category"), row.get("scheme")), [])
        dtypes = {member.get("stored_dtype") for member in members}
        if len(members) == row.get("count") and len(dtypes) == 1 and all(isinstance(member.get("physical_bytes"), int) for member in members):
            row["stored_dtype"] = next(iter(dtypes))
            row["stored_header_count"] = len(members)
            row["physical_bytes"] = sum(int(member["physical_bytes"]) for member in members)
            row["logical_elements"] = sum(int(member["logical_elements"]) for member in members)
            row["dtype_coverage"] = "per_tensor"
            row["layer_coverage"] = "complete"
            row["byte_status"] = "measured_sum"
        elif len(dtypes) > 1:
            row["stored_dtype"] = None
            row["physical_bytes"] = None
            row["logical_elements"] = None
            row["dtype_coverage"] = "mixed"
            row["layer_coverage"] = "subset"
            row["byte_status"] = "mixed_stored_dtype"
        else:
            row["stored_dtype"] = None
            row["physical_bytes"] = None
            row["logical_elements"] = None
            row["dtype_coverage"] = "absent"
            row["layer_coverage"] = "subset" if members else "absent"
            row["byte_status"] = "partial_members"


def apply_archive_roles(modules: list[dict[str, Any]], module_types: Any) -> None:
    roles = module_types if isinstance(module_types, Mapping) else {}
    for row in modules:
        if row.get("role") != "weight":
            continue
        pairs = roles.get(_role_key(str(row.get("category") or ""), "weight"))
        matched: list[tuple[str, int]] = []
        if isinstance(pairs, Mapping):
            for label, count in pairs.items():
                if not isinstance(label, str) or isinstance(count, bool) or not isinstance(count, int):
                    continue
                scheme, sep, dtype = label.partition("|")
                if sep and scheme == row.get("scheme") and dtype:
                    matched.append((dtype, count))
        row["physical_bytes"] = None
        row["logical_elements"] = None
        row["layer_coverage"] = "subset"
        if len(matched) == 1 and matched[0][1] == row.get("count"):
            row["stored_dtype"] = matched[0][0]
            row["stored_header_count"] = matched[0][1]
            row["dtype_coverage"] = "role_aggregate"
            row["byte_status"] = "category_count_is_not_bytes"
        elif len(matched) > 1:
            row["stored_dtype"] = None
            row["dtype_coverage"] = "mixed"
            row["byte_status"] = "mixed_stored_dtype"
        elif len(matched) == 1:
            row["stored_dtype"] = None
            row["dtype_coverage"] = "absent"
            row["byte_status"] = "header_count_disagrees"
        else:
            row["stored_dtype"] = None
            row["dtype_coverage"] = "absent"
            row["byte_status"] = "header_role_absent"


def counts_from_groups(groups: Any) -> dict[str, int] | None:
    if not isinstance(groups, Mapping):
        return None
    counts: dict[str, int] = {}
    for label, count in groups.items():
        if not isinstance(label, str) or isinstance(count, bool) or not isinstance(count, int) or "|" not in label:
            continue
        dtype = label.split("|", 1)[1]
        if dtype:
            counts[dtype] = counts.get(dtype, 0) + count
    return counts


def counts_from_tensors(tensors: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tensor in tensors:
        dtype = tensor.get("stored_dtype")
        if isinstance(dtype, str):
            counts[dtype] = counts.get(dtype, 0) + 1
    return counts


def weight_key_count(description: Mapping[str, Any]) -> int:
    return sum(1 for key, value in description.items() if isinstance(key, str) and key.endswith(".weight") and isinstance(value, str))


def _role_key(category_name: str, role_name: str) -> str:
    parts: list[str] = []
    for part in category_name.split("."):
        if not part:
            continue
        parts.append(part)
        if part in _INDEXED_TOKENS:
            parts.append("*")
    suffix = {"weight": "weight", "scale": "weight_scale", "bias": "bias"}.get(role_name)
    if suffix:
        parts.append(suffix)
    return ".".join(parts)
