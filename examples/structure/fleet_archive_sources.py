"""Source discovery for DSH, Wave 5, and extended archive cases.

Receipt indexes, kernel identity, and producer workload files live here.
Geometry decisions stay in fleet_archive_case. The normal entry scans the
canonical extraction roots from fleet_source_discovery. The task-local TSV is
used only when configure_archive_roots is given that path. Timing fields are
not read.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

_STRUCT = Path(__file__).resolve().parent
_DEFAULT_DATA_ROOTS = (Path("/Volumes/data/mindie-sim-data"), Path("/Users/maoxx241/code/mindie-agent/.workstreams"))
_DEFAULT_RESULTS = _STRUCT / "results"
_DEFAULT_CASES = _STRUCT / "cases"
_DEFAULT_ARCHIVE = Path("/Volumes/data/mindie-sim-data/acceptance-archives-20261030")
_DEFAULT_RECEIPT_INDEX = Path("/tmp/mindie-3h-20261111/observation_receipt_index.tsv")
_MAX_RECEIPT_BYTES = 4 * 1024 * 1024
_GEOM_KEYS = (
    "query_rows", "sequences_per_replica", "tokens_per_sequence", "context_tokens",
    "context_basis", "batch_basis", "output_query_rows",
)
_DECL_KEYS = ("name", "layers", "hidden_size", "vocab_size", "tp")
_CANONICAL = (
    ("dsh-full-generalization", "extractions"),
    ("wave5-eval", "a2", "extractions"),
    ("wave5-eval", "a3", "extractions"),
    ("wave5-eval", "a5", "cache"),
    ("wave5-eval", "a5", "extractions"),
)
_IDENT = re.compile(r'"source_identity"\s*:\s*\{([^{}]{0,4000})\}')

_ROOTS: dict[str, Any] | None = None
_REGISTRY: dict[str, Any] | None = None
_RECEIPTS: dict[str, list[str]] | None = None
_SOURCE_SHA: dict[str, list[str]] | None = None
_CASES: dict[str, dict[str, Any]] | None = None
_PROJECTION: dict[str, dict[str, Any]] = {}
_SHA: dict[str, str] = {}


def configure_roots(*, data_roots=None, results_dir=None, cases_dir=None,
                    archive_root=None, receipt_index=None, cases_index=None) -> None:
    """Retarget registry, archive, and receipt roots, then drop caches."""
    global _ROOTS
    _ROOTS = {
        "data_roots": tuple(Path(p) for p in (data_roots if data_roots is not None else _DEFAULT_DATA_ROOTS)),
        "results": Path(results_dir) if results_dir else _DEFAULT_RESULTS,
        "cases": Path(cases_dir) if cases_dir else _DEFAULT_CASES,
        "archive": Path(archive_root) if archive_root else _DEFAULT_ARCHIVE,
        "receipt_index": Path(receipt_index) if receipt_index else None,
        "cases_index": Path(cases_index) if cases_index else (_STRUCT / "cases.json"),
    }
    clear_caches()


def clear_caches() -> None:
    """Drop registry, receipt, producer, and hash caches."""
    global _REGISTRY, _RECEIPTS, _CASES, _SOURCE_SHA
    _REGISTRY = None
    _RECEIPTS = None
    _CASES = None
    _SOURCE_SHA = None
    _PROJECTION.clear()
    _SHA.clear()
    from fleet_archive_producer import clear_producer_caches
    clear_producer_caches()


def roots() -> dict[str, Any]:
    global _ROOTS
    if _ROOTS is None:
        configure_roots()
    return _ROOTS


def as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value == int(value):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def sha256(path: Path) -> str:
    key = str(path)
    cached = _SHA.get(key)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    value = digest.hexdigest()
    _SHA[key] = value
    return value


def content_sha(path: Path) -> str | None:
    """SHA-256 of kernel text. Gzip members are hashed uncompressed."""
    if not path.name.endswith(".gz"):
        try:
            return sha256(path)
        except OSError:
            return None
    key = f"content:{path}"
    cached = _SHA.get(key)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    try:
        with gzip.open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except (OSError, EOFError, gzip.BadGzipFile):
        return None
    value = digest.hexdigest()
    _SHA[key] = value
    return value


def rel_keys(path: str) -> set[str]:
    keys = {path, str(Path(path))}
    for root in roots()["data_roots"]:
        prefix = str(root).rstrip("/") + "/"
        if path.startswith(prefix):
            keys.add(path[len(prefix):])
    marker = "/mindie-sim-data/"
    if marker in path:
        keys.add(path.split(marker, 1)[1])
    return {key for key in keys if key}


def suffix(path: str) -> str:
    keys = rel_keys(path)
    keys.discard(path)
    keys.discard(str(Path(path)))
    return sorted(keys, key=len)[0] if keys else path


def registry() -> dict[str, dict[str, Any]]:
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    index: dict[str, dict[str, Any]] = {}
    results = roots()["results"]
    _load_dsh(results / "dsh_full_generalization.json", index)
    _load_wave5(results / "wave5_full_generalization.json", index)
    by_path: dict[str, dict[str, Any]] = {}
    for record in index.values():
        raw = str(record.get("source_path") or "")
        for key in rel_keys(raw):
            by_path.setdefault(key, record)
        if raw and Path(raw).is_file():
            by_path.setdefault(str(Path(raw).resolve()), record)
    _REGISTRY = index
    _REGISTRY["__by_path__"] = by_path  # type: ignore[assignment]
    return _REGISTRY


def _structural_registry_record(**fields: Any) -> dict[str, Any]:
    fields["source_path"] = fields.pop("source")
    return fields


def _load_dsh(path: Path, index: dict[str, dict[str, Any]]) -> None:
    if not path.is_file():
        return
    document = json.loads(path.read_text(encoding="utf-8"))
    provenance = document.get("calibration_provenance") if isinstance(document.get("calibration_provenance"), Mapping) else {}
    relation = provenance.get("evaluation_relation")
    independent = provenance.get("independent_heldout")
    for item in document.get("heldout_cases") or ():
        if not isinstance(item, Mapping):
            continue
        source = str(item.get("path") or "")
        traits = item.get("traits") if isinstance(item.get("traits"), Mapping) else {}
        record = _structural_registry_record(
            source=source, suite="dsh_20261030_heldout", capture_id=f"dsh_heldout:{suffix(source)}",
            phase=traits.get("phase"), template=item.get("template"), family=traits.get("family"),
            hw=traits.get("hw"), parallel={axis: as_int(traits.get(axis)) for axis in ("tp", "dp", "ep")},
            layers=as_int(traits.get("num_layers") or traits.get("layers")),
            experts=as_int(traits.get("num_experts")), top_k=as_int(traits.get("top_k")),
            relation=relation if isinstance(relation, str) else None,
            independent=independent if isinstance(independent, bool) else None,
            generator={"schema_version": document.get("schema_version")},
            cross_tp=bool(item.get("cross_tp_transfer")),
        )
        index[record["capture_id"]] = record


def _load_wave5(path: Path, index: dict[str, dict[str, Any]]) -> None:
    if not path.is_file():
        return
    document = json.loads(path.read_text(encoding="utf-8"))
    chips = document.get("chip_report_identities") if isinstance(document.get("chip_report_identities"), Mapping) else {}
    cohorts = {}
    for cohort in document.get("cohort_summaries") or ():
        if isinstance(cohort, Mapping) and cohort.get("cohort"):
            proven = cohort.get("calibration_provenance") if isinstance(cohort.get("calibration_provenance"), Mapping) else {}
            cohorts[str(cohort["cohort"])] = proven
    for item in document.get("cases") or ():
        if not isinstance(item, Mapping):
            continue
        hw = str(item.get("hw") or "")
        cohort = str(item.get("cohort") or "")
        cell = str(item.get("cell") or "")
        chip = chips.get(hw) if isinstance(chips.get(hw), Mapping) else {}
        proven = cohorts.get(cohort) or {}
        relation = proven.get("evaluation_relation")
        fitted = bool(proven.get("target_timing_used_to_fit") or proven.get("heldout_observed_values_used_in_fit"))
        record = _structural_registry_record(
            source=str(item.get("path") or ""), suite="wave5_20261031",
            capture_id=f"wave5:{hw}:{cohort}:{cell}", phase=item.get("phase"),
            template=item.get("template"), family=item.get("family"), hw=hw,
            parallel={axis: as_int(item.get(axis)) for axis in ("tp", "dp", "ep")},
            layers=as_int(item.get("num_layers")), experts=as_int(item.get("num_experts")),
            top_k=as_int(item.get("top_k")),
            relation=relation if isinstance(relation, str) else None,
            independent=False if fitted or (isinstance(relation, str) and "in_sample" in relation) else None,
            generator={
                "schema_version": document.get("schema_version"),
                "sim_identity": chip.get("sim_identity") or document.get("sim_identity"),
                "parser_identity": chip.get("parser_identity") or document.get("parser_identity"),
                "chip_schema": chip.get("schema_version"),
            },
            cross_tp=False,
        )
        index[record["capture_id"]] = record


def receipt_index() -> dict[str, list[str]]:
    """Map a source path to every receipt. An explicit TSV overrides the canonical scan."""
    global _RECEIPTS, _SOURCE_SHA
    if _RECEIPTS is not None:
        return _RECEIPTS
    index: dict[str, list[str]] = {}
    sha_index: dict[str, list[str]] = {}
    path = roots()["receipt_index"]
    if isinstance(path, Path) and path.is_file():
        _load_receipt_tsv(path, index, sha_index)
    else:
        _scan_canonical(index, sha_index)
    _RECEIPTS = index
    _SOURCE_SHA = sha_index
    return index


def _load_receipt_tsv(path: Path, index: dict[str, list[str]], sha_index: dict[str, list[str]]) -> None:
    with path.open(encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        if "source_path" not in header or "receipt" not in header:
            return
        source_at, receipt_at = header.index("source_path"), header.index("receipt")
        sha_at = header.index("source_sha256") if "source_sha256" in header else None
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(source_at, receipt_at):
                continue
            receipt = parts[receipt_at]
            if "/pred_" in receipt or Path(receipt).name.startswith("pred_"):
                continue
            source = parts[source_at]
            for key in rel_keys(source):
                bucket = index.setdefault(key, [])
                if receipt not in bucket:
                    bucket.append(receipt)
            if sha_at is not None and len(parts) > sha_at and re.fullmatch(r"[0-9a-f]{64}", parts[sha_at]):
                owners = sha_index.setdefault(parts[sha_at], [])
                if source not in owners:
                    owners.append(source)


def _canonical_dirs() -> list[Path]:
    """E4's declared roots when the archive is the canonical tree; else the same relative layout."""
    archive = roots()["archive"]
    try:
        from fleet_source_discovery import ARCHIVE_ROOT, DEFAULT_ROOTS
    except ImportError:
        ARCHIVE_ROOT, DEFAULT_ROOTS = None, ()
    if ARCHIVE_ROOT is not None and archive == Path(ARCHIVE_ROOT):
        folders = [Path(item) for item in DEFAULT_ROOTS]
        extra = Path(ARCHIVE_ROOT) / "wave5-eval" / "a5" / "extractions"
        if extra not in folders:
            folders.append(extra)
        return folders
    return [archive.joinpath(*parts) for parts in _CANONICAL]


def _scan_canonical(index: dict[str, list[str]], sha_index: dict[str, list[str]]) -> None:
    for folder in _canonical_dirs():
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            if not path.is_file() or path.suffix != ".json" or path.name.startswith("pred_"):
                continue
            try:
                if path.stat().st_size > _MAX_RECEIPT_BYTES:
                    continue
                with path.open("rb") as handle:
                    head = handle.read(65536).decode("utf-8", "ignore")
            except OSError:
                continue
            match = _IDENT.search(head)
            if not match:
                continue
            body = match.group(1)
            found = re.search(r'"path"\s*:\s*"([^"]+)"', body)
            digest = re.search(r'"sha256"\s*:\s*"([0-9a-fA-F]{64})"', body)
            if not found:
                continue
            source = found.group(1)
            receipt = str(path)
            for key in rel_keys(source):
                bucket = index.setdefault(key, [])
                if receipt not in bucket:
                    bucket.append(receipt)
            if digest:
                owners = sha_index.setdefault(digest.group(1).lower(), [])
                if source not in owners:
                    owners.append(source)


def case_index() -> dict[str, dict[str, Any]]:
    global _CASES
    if _CASES is not None:
        return _CASES
    index: dict[str, dict[str, Any]] = {}
    path = roots()["cases_index"]
    if path.is_file():
        document = json.loads(path.read_text(encoding="utf-8"))
        for entry in document.get("cases") or ():
            if not isinstance(entry, Mapping):
                continue
            source = entry.get("source") if isinstance(entry.get("source"), Mapping) else {}
            model = entry.get("model_declaration") if isinstance(entry.get("model_declaration"), Mapping) else {}
            calibration = entry.get("calibration") if isinstance(entry.get("calibration"), Mapping) else {}
            fitted = calibration.get("target_timing_used_to_fit")
            if not isinstance(fitted, bool):
                fitted = entry.get("target_timing_used_to_fit") if isinstance(entry.get("target_timing_used_to_fit"), bool) else None
            record = {
                "case_id": entry.get("case_id") or entry.get("id"),
                "phase": entry.get("phase"),
                "source_path": source.get("path"),
                "source_sha256": source.get("sha256"),
                "model_path": model.get("path"),
                "model_sha256": model.get("sha256"),
                "extraction_path": entry.get("extraction_path"),
                "evaluation_relation": calibration.get("evaluation_relation"),
                "target_timing_used_to_fit": fitted,
                "calibration_origin": calibration.get("origin") or entry.get("calibration_origin"),
            }
            for key in rel_keys(str(source.get("path") or "")):
                index[key] = record
            if isinstance(source.get("sha256"), str):
                index[f"sha:{source['sha256']}"] = record
    _CASES = index
    return index


def project_receipt(path: Path) -> dict[str, Any]:
    key = str(path)
    cached = _PROJECTION.get(key)
    if cached is not None:
        return cached
    if not path.is_file():
        projected: dict[str, Any] = {"status": "missing", "path": key}
    elif path.stat().st_size > _MAX_RECEIPT_BYTES or path.name.startswith("pred_"):
        projected = {"status": "rejected", "path": key, "reason": "pred_or_over_bound"}
    else:
        document = json.loads(path.read_text(encoding="utf-8"))
        observed = document.get("observed") if isinstance(document, Mapping) and isinstance(document.get("observed"), Mapping) else document
        projected = {"status": "unreadable", "path": key}
        if isinstance(observed, Mapping):
            identity = observed.get("source_identity") if isinstance(observed.get("source_identity"), Mapping) else {}
            declaration = observed.get("model_declaration") if isinstance(observed.get("model_declaration"), Mapping) else {}
            meta = document.get("meta") if isinstance(document, Mapping) and isinstance(document.get("meta"), Mapping) else {}
            projected = {
                "status": "projected", "path": key,
                "cache_version": document.get("cache_version") if isinstance(document, Mapping) else None,
                "parser_identity": document.get("parser_identity") if isinstance(document, Mapping) else None,
                "phase": observed.get("phase"),
                "source_path": identity.get("path"), "source_sha256": identity.get("sha256"),
                "source_size": as_int(identity.get("size_bytes")),
                "model_declaration": {name: declaration.get(name) for name in _DECL_KEYS if name in declaration},
                "populations": _populations(observed),
                "receipt_windows": _receipt_windows(observed),
                "client": _client(meta.get("client")),
                "context_evidence": _context_evidence(meta.get("context_evidence")),
            }
        del document
    _PROJECTION[key] = projected
    return projected


def _client(raw: Any) -> dict[str, int]:
    if not isinstance(raw, Mapping):
        return {}
    return {key: value for key in ("input_len", "concurrency", "output_tokens") if (value := as_int(raw.get(key))) is not None}


def _context_evidence(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return {}
    kept: dict[str, Any] = {}
    for key in ("representative_tokens", "lower_bound_tokens", "upper_bound_tokens", "requested_prefix_tokens", "requested_suffix_tokens"):
        number = as_int(raw.get(key))
        if number is not None or key in raw:
            kept[key] = number if number is not None or raw.get(key) is None else raw.get(key)
    if isinstance(raw.get("basis"), str):
        kept["basis"] = raw["basis"]
    if isinstance(raw.get("per_step_context_observed"), bool):
        kept["per_step_context_observed"] = raw["per_step_context_observed"]
    if isinstance(raw.get("client_token_exact"), bool):
        kept["client_token_exact"] = raw["client_token_exact"]
    if isinstance(raw.get("limitation"), str):
        kept["limitation"] = raw["limitation"]
    identity = raw.get("source_identity") if isinstance(raw.get("source_identity"), Mapping) else {}
    if identity.get("path"):
        kept["source_path"] = identity.get("path")
    if isinstance(identity.get("sha256"), str):
        kept["source_sha256"] = identity["sha256"]
    size = as_int(identity.get("size_bytes"))
    if size is not None:
        kept["source_size"] = size
    return kept


def _populations(observed: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups = observed.get("geometry_groups")
    populations: list[dict[str, Any]] = []
    if isinstance(groups, list) and groups:
        for group in groups:
            if not isinstance(group, Mapping):
                continue
            geometry = group.get("geometry") if isinstance(group.get("geometry"), Mapping) else {}
            item = _geometry_item(geometry, observed.get("phase"))
            item["rank_id"] = str(group.get("rank_id") or "")
            item["device_id"] = str(group.get("device_id") or "")
            item["forward_count"] = len(group.get("forward_ids") or ())
            populations.append(item)
        return populations
    counts: dict[tuple, int] = {}
    ranks: dict[tuple, tuple[str, str]] = {}
    for forward in observed.get("forwards") or ():
        if not isinstance(forward, Mapping):
            continue
        geometry = forward.get("geometry") if isinstance(forward.get("geometry"), Mapping) else {}
        item = _geometry_item(geometry, forward.get("phase") or observed.get("phase"))
        if item.get("query_rows") is None:
            item["query_rows"] = as_int(forward.get("query_rows"))
        key = tuple(item.get(name) for name in ("phase", "query_rows", "sequences_per_replica", "tokens_per_sequence", "context_tokens", "context_basis", "batch_basis"))
        counts[key] = counts.get(key, 0) + 1
        ranks[key] = (str(forward.get("rank_id") or ""), str(forward.get("device_id") or ""))
    for key, count in counts.items():
        phase, query, sequences, tokens, context, context_basis, batch_basis = key
        rank, device = ranks[key]
        populations.append({
            "phase": phase, "query_rows": query, "sequences_per_replica": sequences,
            "tokens_per_sequence": tokens, "context_tokens": context, "context_basis": context_basis,
            "batch_basis": batch_basis, "rank_id": rank, "device_id": device, "forward_count": count,
        })
    return populations


def _geometry_item(geometry: Mapping[str, Any], phase: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"phase": phase if isinstance(phase, str) else None}
    for key in _GEOM_KEYS:
        if key in ("context_basis", "batch_basis"):
            value = geometry.get(key)
            if isinstance(value, str):
                item[key] = value
            continue
        number = as_int(geometry.get(key))
        if number is not None or key == "context_tokens":
            item[key] = number
    return item


def signature(projected: Mapping[str, Any]) -> tuple:
    declaration = tuple((key, projected.get("model_declaration", {}).get(key)) for key in _DECL_KEYS)
    populations = tuple(sorted(
        (item.get("rank_id"), item.get("device_id"), item.get("phase"), item.get("query_rows"),
         item.get("sequences_per_replica"), item.get("tokens_per_sequence"), item.get("context_tokens"),
         item.get("context_basis"), item.get("batch_basis"), item.get("forward_count"))
        for item in projected.get("populations") or ()
    ))
    return (projected.get("phase"), declaration, populations)


def locate_kernels(rel: str) -> list[Path]:
    if not rel:
        return []
    found = _kernels_under(rel)
    if found:
        return found
    stripped = re.sub(r"#\d+$", "", rel)
    return _kernels_under(stripped) if stripped != rel else []


def _kernels_under(rel: str) -> list[Path]:
    found: list[Path] = []
    for root in roots()["data_roots"]:
        direct = root / rel
        candidates = [direct] if direct.suffix else []
        parent = direct if direct.is_dir() else direct.parent
        for name in ("kernel_details.csv", "kernel_details.csv.gz"):
            candidates.append(parent / name)
        for candidate in candidates:
            if candidate.is_file():
                resolved = candidate.resolve()
                if resolved not in found:
                    found.append(resolved)
    return found


def classify_kernels(paths: list[Path]) -> tuple[Path, dict | None, dict | None] | dict[str, Any]:
    if len(paths) > 1:
        digests = [content_sha(path) for path in paths]
        if any(item is None for item in digests):
            return {"diagnostics": ["kernel_unreadable"], "needed": ["readable kernel_details"]}
        if len(set(digests)) != 1:
            return {"diagnostics": ["kernel_serializations_disagree"], "needed": ["one uncompressed kernel sha256"],
                    "source": {"path": str(paths[0]), "sha256": None, "size_bytes": None, "sha256_verified": False}}
    hits = []
    by_path = registry().get("__by_path__", {})
    for path in paths:
        canonical = by_path.get(str(path)) or by_path.get(suffix(str(path)))
        registered = case_index().get(str(path)) or case_index().get(suffix(str(path)))
        if canonical is not None or registered is not None:
            hits.append((path, canonical, registered))
    identities = {
        (item[1].get("capture_id") if isinstance(item[1], dict) else None,
         item[2].get("case_id") if isinstance(item[2], dict) else None)
        for item in hits
    }
    if len(identities) > 1:
        return {"diagnostics": ["kernel_joins_disagree"], "needed": ["one registry or registered case"]}
    if hits:
        return hits[0]
    sha_hits: list[tuple[Path, dict | None, dict | None]] = []
    for path in paths:
        digest = sha256(path)
        for record in records_for_sha(digest):
            sha_hits.append((path, record, None))
        registered = case_index().get(f"sha:{digest}")
        if registered is not None:
            sha_hits.append((path, None, registered))
    registry_ids = {item[1]["capture_id"] for item in sha_hits if item[1]}
    case_ids = {item[2].get("case_id") for item in sha_hits if item[2]}
    if len(registry_ids) > 1 or len(case_ids) > 1 or (registry_ids and case_ids):
        return {"diagnostics": ["sha_matches_multiple_sources"], "needed": ["one physical source"]}
    for item in sha_hits:
        if item[1] is not None:
            return item
    if sha_hits:
        return sha_hits[0]
    source_path = paths[0]
    return {"diagnostics": ["extended_source_has_no_structural_declaration"],
            "needed": ["extraction receipt or registered case"],
            "source": {"path": str(source_path), "sha256": sha256(source_path), "size_bytes": source_path.stat().st_size, "sha256_verified": False}}


def _receipt_windows(observed: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Identity of each receipt forward. Span times and activity totals are not copied."""
    rows: list[dict[str, Any]] = []
    for forward in observed.get("forwards") or ():
        if not isinstance(forward, Mapping):
            continue
        body = forward.get("body") if isinstance(forward.get("body"), Mapping) else {}
        geometry = forward.get("geometry") if isinstance(forward.get("geometry"), Mapping) else {}
        device = forward.get("device_id")
        if device in (None, ""):
            device = body.get("device_id")
        rank = forward.get("rank_id") if forward.get("rank_id") is not None else body.get("rank_id")
        query = as_int(forward.get("query_rows"))
        if query is None:
            query = as_int(geometry.get("query_rows"))
        row: dict[str, Any] = {
            "forward_id": forward.get("forward_id"), "phase": forward.get("phase"),
            "rank_id": rank, "device_id": None if device in (None, "") else str(device), "query_rows": query,
        }
        for key in ("dp", "dp_rank", "cohort", "cohort_id"):
            if key in forward or key in geometry:
                row[key] = forward[key] if key in forward else geometry.get(key)
        rows.append(row)
    return rows


def _window_key(row: Mapping[str, Any]) -> tuple:
    return tuple(row.get(name) for name in ("forward_id", "phase", "rank_id", "device_id", "query_rows", "dp", "dp_rank", "cohort", "cohort_id"))


def agreed_receipt_windows(projections: list[Mapping[str, Any]]) -> tuple[list[dict[str, Any]] | None, str | None]:
    lists = [item["receipt_windows"] for item in projections if isinstance(item.get("receipt_windows"), list) and item["receipt_windows"]]
    if not lists:
        return None, None
    first = [_window_key(row) for row in lists[0]]
    if any([_window_key(row) for row in other] != first for other in lists[1:]):
        return None, "receipt_window_identities_disagree"
    return [dict(row) for row in lists[0]], None


def capture_sizes(text: str) -> list[int] | None:
    match = re.search(r'"cudagraph_capture_sizes"\s*:\s*\[([0-9,\s]+)\]', text)
    if not match:
        return None
    found = [int(item) for item in match.group(1).split(",") if item.strip().isdigit()]
    return found or None


def device_inventory(documents: Mapping[str, Any]) -> dict[str, Any]:
    """Host and npu strings retained on this run. A missing serial stays missing."""
    env = documents.get("meta_env") if isinstance(documents.get("meta_env"), Mapping) else {}
    run = documents.get("run_meta") if isinstance(documents.get("run_meta"), Mapping) else {}
    keys: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            keys.update(str(key) for key in value)
            for child in value.values():
                walk(child)

    walk(run)
    retained = sorted(key for key in keys if "serial" in key.lower() or key.lower() in {"driver", "driver_version", "deviceinfo", "device_info", "chip_id", "hostname"})
    label = env.get("NPU_TYPE") or run.get("npu_type")
    return {
        "meta_env": env.get("NPU_TYPE") or None, "run_meta": run.get("npu_type") or None,
        "host": run.get("host") or env.get("HOST") or None,
        "timestamp_utc": run.get("timestamp_utc") if isinstance(run.get("timestamp_utc"), str) else None,
        "physical_serial": None, "driver": None, "device_info_retained": bool(retained),
        "same_run_inventory_keys": retained,
        "label_role": "producer_deployment_setting" if isinstance(label, str) and label else None,
        "measured_from_npu_smi": False,
    }


def annotate_public_frames(frames, projections, launch, notes):
    """Attach receipt identity and the executed graph bucket. The bucket is not a KV context."""
    windows, note = agreed_receipt_windows(projections)
    if note:
        notes.append(note)
    mode = launch.get("graph_capture_mode") if isinstance(launch, Mapping) else None
    raw_sizes = launch.get("graph_capture_sizes") if isinstance(launch, Mapping) else None
    sizes = [item for item in raw_sizes if isinstance(item, int)] if isinstance(raw_sizes, list) else []
    identity = bool(frames) and all(
        isinstance(item, Mapping) and item.get("schedule_role") == "model_argument_identity" for item in frames
    )
    aligned = None if identity else (windows if windows and frames and len(windows) == len(frames) else None)
    if not identity and windows and frames and len(windows) != len(frames):
        notes.append(f"receipt_window_count_{len(windows)}_disagrees_with_frames_{len(frames)}")
    elif windows and not frames:
        notes.append(f"receipt_window_count_{len(windows)}_disagrees_with_frames_0")
    mismatch = False
    bound = []
    for index, frame in enumerate(frames or ()):
        item = dict(frame)
        window = aligned[index] if aligned else None
        if window:
            item["receipt_forward_id"] = window.get("forward_id")
            item["receipt_rank_id"] = window.get("rank_id")
            item["receipt_device_id"] = window.get("device_id")
            item["receipt_query_rows"] = window.get("query_rows")
            if window.get("query_rows") not in (None, item.get("query_rows")):
                mismatch = True
        query = item.get("query_rows")
        if sizes and mode and isinstance(query, int):
            fits = [item for item in sizes if item >= query]
            if fits:
                item["graph_capture_mode"] = mode
                item["graph_capture_bucket"] = min(fits)
                item["graph_bucket_bounds_query_not_context"] = True
        bound.append(item)
    if mismatch:
        notes.append("receipt_query_disagrees_with_executed_query")
    if windows and all(row.get("dp") is None and row.get("dp_rank") is None for row in windows):
        notes.append("per_window_dp_absent")
    if windows and all(row.get("cohort") is None and row.get("cohort_id") is None for row in windows):
        notes.append("per_window_cohort_absent")
    executed = None
    if bound and mode and sizes:
        buckets = {item.get("graph_capture_bucket") for item in bound if item.get("graph_capture_bucket") is not None}
        contexts = [item["context_tokens"] for item in bound if isinstance(item.get("context_tokens"), int)]
        queries = {item.get("query_rows") for item in bound}
        executed = {
            "mode": mode, "capture_sizes": sizes, "source": "compilation_config.cudagraph_capture_sizes",
            "executed_query_rows": next(iter(queries)) if len(queries) == 1 else None,
            "graph_capture_bucket": next(iter(buckets)) if len(buckets) == 1 else None,
            "bucket_bounds": "query_not_kv_context", "selected": False,
            "context_tokens_min": min(contexts) if contexts else None,
            "context_tokens_max": max(contexts) if contexts else None,
        }
    coverage = {
        "receipt_window_count": len(windows) if windows else 0,
        "per_window_query": bool(windows) and all(isinstance(row.get("query_rows"), int) for row in windows),
        "per_window_dp": bool(windows) and any(row.get("dp") is not None or row.get("dp_rank") is not None for row in windows),
        "per_window_cohort": bool(windows) and any(row.get("cohort") is not None or row.get("cohort_id") is not None for row in windows),
        "deployment_dp": launch.get("dp") if isinstance(launch, Mapping) else None,
        "deployment_dp_per_window": False,
        "identified_declaration_count": len(frames) if identity else 0,
        "step_frame_count": 0 if identity else len(frames or ()),
        "unpaired_receipt_window_count": len(windows) if windows and aligned is None else 0,
        "count_mismatch_rejects_declaration": False,
    }
    return bound, executed, windows, coverage


_DECLARED_CATALOG = {"Ascend950PR_A5": "Ascend950PR_9579"}


def _supply_line(sku: str) -> str | None:
    text = str(sku or "")
    if "950PR" in text:
        return "A5PR"
    if "950DT" in text:
        return "A5DT"
    if text.startswith("Ascend910B"):
        return "A2"
    if text.startswith("Ascend910_93"):
        return "A3"
    return "A5" if text.startswith(("Ascend950", "Ascend910_95")) else None


def declared_hardware(machine, npu):
    """One agreed producer npu string becomes its catalog sku. That is declared, not serial-verified."""
    if not isinstance(machine, dict) or not isinstance(npu, dict):
        return machine, None
    declared = [value for value in dict.fromkeys((npu.get("meta_env"), npu.get("run_meta"))) if isinstance(value, str) and value]
    template = machine.get("sku") if isinstance(machine.get("sku"), str) else ""
    rows = [{"declared_identity": item, "catalog_sku": _DECLARED_CATALOG.get(item), "source": "meta.env:NPU_TYPE+run_meta.npu_type",
             "host": npu.get("host"), "role": "producer_deployment_setting", "priority": 1,
             "applied": len(declared) == 1 and item in _DECLARED_CATALOG, "exact": False, "equipment_proof": None} for item in declared]
    mapped = {row["catalog_sku"] for row in rows}
    if template and template not in declared and template not in mapped:
        own = _supply_line((rows[0]["catalog_sku"] or rows[0]["declared_identity"]) if len(rows) == 1 else "")
        other = _supply_line(template)
        rows.append({"declared_identity": template, "catalog_sku": template, "host": None, "priority": 2, "applied": False,
                     "exact": False, "equipment_proof": None,
                     "source": "template_machine.sku+eval_a5_wave5.HW_A5" if template == "Ascend950DT_9582" else "template_machine.sku",
                     "role": "contrary_template" if own and other and own != other else "template_subtype_not_measurement"})
    applied = [row for row in rows if row["applied"]]
    if len(applied) == 1:
        cleaned = dict(machine)
        cleaned["sku"] = applied[0]["catalog_sku"]
        return cleaned, rows
    if len(rows) < 2:
        return machine, None
    cleaned = dict(machine)
    cleaned.pop("sku", None)
    return cleaned, rows


def conditional_scenarios(case, candidates):
    """One parseable case per applied catalogue sku. A contrary template stays audit-only."""
    if not isinstance(case, Mapping) or not isinstance(candidates, list):
        return None
    scenarios = []
    for row in candidates:
        if not isinstance(row, Mapping):
            continue
        sku = row.get("catalog_sku") if isinstance(row.get("catalog_sku"), str) and row.get("catalog_sku") else None
        applied = row.get("applied") is not False
        scenario = {
            "declared_identity": row.get("declared_identity"), "catalog_sku": sku, "host": row.get("host"),
            "source": row.get("source"), "role": row.get("role"), "priority": row.get("priority"),
            "applied": row.get("applied"), "exact": False, "equipment_proof": None, "selected": False,
            "parseable": bool(sku) and applied,
        }
        if sku and applied:
            copied = json.loads(json.dumps(case))
            machine = dict(copied.get("machine") or {})
            machine["sku"] = sku
            copied["machine"] = machine
            scenario["case"] = copied
        else:
            scenario["reason"] = "declared_identity_has_no_catalog_sku" if not sku else (row.get("role") or "not_applied")
        scenarios.append(scenario)
    return scenarios or None


def records_for_sha(digest: str) -> list[dict[str, Any]]:
    receipt_index()
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    by_path = registry().get("__by_path__", {})
    for raw in (_SOURCE_SHA or {}).get(digest, ()):
        record = by_path.get(raw) or by_path.get(suffix(str(raw)))
        capture = record.get("capture_id") if isinstance(record, dict) else None
        if isinstance(capture, str) and capture not in seen:
            seen.add(capture)
            found.append(record)
    return found


