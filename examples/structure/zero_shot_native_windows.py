"""Independent native-window source for the original 731 zero-shot rows.

[Role]
  Resolve one original enrolled zero-shot row to every retained raw
  ``kernel_details.csv(.gz)`` timetable under configurable producer roots and
  publish typed, independently keyed observations.  Decode timetables are
  segmented with the maintained
  :func:`mindie_profiler.decode_segmentation.auto_segment_decode_forwards`;
  prefill timetables use the maintained
  :func:`scoped_native_replay.extract_full_observation` mechanism.  Both paths
  are wrapped by one raw streaming scan that keeps device-span versus additive
  mass, per raw op-type x native accelerator core totals, per-stream spans,
  raw content identity and the found/unknown boundary map.

[Invariants]
  * Segmentation, rank and labels never consume service times, fitted ratios or
    generation-model predictions.  Phase comes from the enrolled row's declared
    phase; a raw trace that does not support it is ``unresolved``/``raw_only``
    rather than relabelled.
  * Discovery uses the producer's on-disk layout only (``out/<case>/<cell>/
    <host>/<worker>/kernel_details.csv.gz`` plus its ``op_statistic.csv`` and
    launch/preflight declarations).  No task-local TSV/map is read at runtime.
  * Rank is derived from the actual immutable launch declaration of that host
    (``--data-parallel-start-rank`` x ``--tensor-parallel-size`` + the raw
    device id) and is cross-checked against the worker directory label when one
    exists.  A conflict or missing declaration is explicit, never guessed.
  * Hardware comes from the same node's preflight ``npu-smi`` declaration, not
    from a cell-id suffix, case title or simulated case.
  * The deployed model is bound from the capture's ``status.preflight[].cfg``
    to a retained weight ``config.json`` with the exact content SHA.  Geometry
    and layer count come from that config; the launch ``spec.model`` directory
    is retained as the quantization namespace.  The enrolled ``model_case``
    catalog label is never used as a similarly named template fallback.
  * Identity is the decompressed raw CSV digest, not the gzip container SHA.
    Producer ``CELL ... export=[(host,size)]`` receipts classify every retained
    trace as actual / shared_payload / stale_superseded / other_trace /
    receipt_unavailable; shared physical payloads never count as independent
    sources, and a stale tag is preserved in inventory with its evidence.
  * Multiple raw traces for one enrolled ID are preserved as distinct
    timetables.  Each keeps its own streamed content SHA-256, header signature,
    rank/device, selected time and found/unknown boundaries.
  * Per-rank observations remain usable on their own; a missing head, layer,
    phase or global client key never erases the raw trace/operator evidence.
  * Iteration is streaming: one timetable is materialised at a time, its
    forwards are bounded by the maintained segmenter, and no global map of the
    retained population is copied.

[Timeouts & Locks]
  Each raw CSV is read with a row budget and wall-clock deadline; no locks,
  subprocesses or device work.

[Side-Effect Policy]
  Read-only over source roots.  Returns frozen records; the caller owns output.
"""
from __future__ import annotations

import csv
from datetime import datetime
import gzip
import hashlib
import json
import re
import tarfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
from mindie_profiler.events import (ProfilerQueryError, ProfilerSchemaError,
                                   ProfilerUsageError, SourceRef)
from mindie_profiler.sources_csv import CsvSource, probe_csv

SCHEMA_VERSION = "mindie-zero-shot-native-windows/1"
DEFAULT_SOURCE_ROOTS = (
    Path("/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack06-20261107"),
    Path("/Volumes/data/mindie-agent-workstreams/a5-multinode-fleet-rack08-20261107"),
)
_PHASES = ("decode", "prefill")
MAX_ROWS = 5_000_000
TIMEOUT_S = 120.0
_MAX_FORWARD_SAMPLES = 3       # maintained segmenter's detailed-forward bound
_MAX_FORWARDS = 4096           # per trace; exceeded -> explicit limit status


def _int(value: Any) -> int | None:
    try:
        out = int(value)
    except (TypeError, ValueError):
        return None
    return out if out >= 0 else None


def _sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


# ---------------------------------------------------------------------------
# Discovery: producer layout, launch declarations, preflight hardware
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CellSource:
    root: Path
    case_dir: Path
    cell_dir: Path
    traces: tuple[Path, ...]


def _cell_id(case: Path, cell: Path) -> str:
    return f"{case.name}_{cell.name}"


@lru_cache(maxsize=16)
def _index(root_names: tuple[str, ...]) -> dict[str, tuple[CellSource, ...]]:
    """Index producer cell directories by enrolled cell id (paths only)."""
    found: dict[str, list[CellSource]] = defaultdict(list)
    for name in root_names:
        root = Path(name)
        out = root / "out"
        if not out.is_dir():
            continue
        for case in sorted(out.iterdir()):
            if not case.is_dir() or case.name.startswith("."):
                continue
            for cell in sorted(case.iterdir()):
                if not cell.is_dir():
                    continue
                traces = tuple(sorted(cell.rglob("kernel_details.csv.gz")))
                found[_cell_id(case, cell)].append(CellSource(root, case, cell, traces))
    return {key: tuple(value) for key, value in found.items()}


def _resolve_roots(roots: Sequence[Path | str] | None) -> tuple[Path, ...]:
    values = DEFAULT_SOURCE_ROOTS if roots is None else tuple(Path(item) for item in roots)
    if not values:
        raise ValueError("native_windows_requires_at_least_one_source_root")
    return values


_LAUNCH_PATTERNS = {
    "dp_start": re.compile(r"--data-parallel-start-rank\s+(\d+)"),
    "dp_local": re.compile(r"--data-parallel-size-local\s+(\d+)"),
    "dp": re.compile(r"--data-parallel-size\s+(\d+)"),
    "tp": re.compile(r"--tensor-parallel-size\s+(\d+)"),
    "pp": re.compile(r"--pipeline-parallel-size\s+(\d+)"),
}
_NPU_ROW = re.compile(r"\|\s*0\s*\|\s*(Ascend[A-Za-z0-9_]+)\s*\|")


@dataclass(frozen=True)
class LaunchDeclaration:
    host: str
    dp_start: int
    dp_local: int
    dp: int | None
    tp: int
    pp: int
    source: str


@lru_cache(maxsize=64)
def _launch(case_dir_name: str) -> dict[str, LaunchDeclaration]:
    """Read the actual serve command retained for each host of one case."""
    case_dir = Path(case_dir_name)
    declared: dict[str, LaunchDeclaration] = {}
    command_dir = case_dir / "cmd"
    if command_dir.is_dir():
        for path in sorted(command_dir.glob("serve_*.sh")):
            host = path.stem.rsplit("_", 1)[-1]
            text = path.read_text(encoding="utf-8", errors="replace")
            values: dict[str, int | None] = {}
            for key, pattern in _LAUNCH_PATTERNS.items():
                matches = pattern.findall(text)
                values[key] = int(matches[-1]) if matches else None
            if values.get("dp_start") is None and values.get("dp_local") is None:
                continue
            declared[host] = LaunchDeclaration(
                host=host,
                dp_start=int(values.get("dp_start") or 0),
                dp_local=int(values.get("dp_local") or 1),
                dp=values.get("dp"),
                tp=int(values.get("tp") or 1),
                pp=int(values.get("pp") or 1),
                source=str(path),
            )
    if declared:
        return declared
    # The case generator's own declaration is the second immutable source.
    case_json = case_dir.parent.parent / "cases" / f"{case_dir.name}.json"
    if not case_json.is_file():
        return {}
    try:
        document = json.loads(case_json.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    nodes = [str(item) for item in document.get("nodes") or ()]
    dp_local = _int(document.get("dp_local"))
    if dp_local is None and nodes:
        dp_local = int(document.get("dp") or 0) // len(nodes) or 1
    if not nodes or not dp_local:
        return {}
    tp = int(document.get("tp") or 1)
    dp = _int(document.get("dp"))
    for ordinal, host in enumerate(nodes):
        declared[host] = LaunchDeclaration(
            host=host, dp_start=ordinal * dp_local, dp_local=dp_local,
            dp=dp, tp=tp, pp=1, source=str(case_json))
    return declared


@lru_cache(maxsize=64)
def _hardware(evidence_name: str) -> dict[str, dict[str, Any]]:
    """Per-node hardware from that node's immutable preflight declaration."""
    path = Path(evidence_name)
    if not path.is_file():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = document if isinstance(document, list) else [document]
    found: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        host = str(entry.get("node") or "")
        raw = str(entry.get("npu_raw") or "")
        match = _NPU_ROW.search(raw)
        found[host] = {
            "hardware_key": match.group(1) if match else None,
            "hostname": entry.get("hostname") or entry.get("host"),
            "image": entry.get("img"),
            "config_sha256": entry.get("cfg"),
            "basis": "preflight_npu_smi" if match else "hardware_not_declared",
        }
    return found


def _launch_for(case_dir: Path, host: str) -> LaunchDeclaration | None:
    return _launch(str(case_dir.resolve())).get(host)


def _parse_utc(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


VERIFIED_PRODUCER_PROBES: dict[str, dict[str, Any]] = {
    "82733cca520bd3f4cbf21db86cef80cd55321659645040251f3bacffa217f325": {
        "role": "fleet_probe_npu_smi_family",
        "family": "Ascend950DT",
        "schema": "fleet_inventory_npu_count_v1",
        "source_line": 46,
    },
}


@lru_cache(maxsize=16)
def _fleet_probe(path_name: str, _stat: tuple[int, int]) -> dict[str, Any]:
    """Verified producer role by canonical source digest, never prose/AST scanning."""
    path = Path(path_name)
    if not path.is_file():
        return {"present": False, "reason": "fleet_probe_missing",
                "path": str(path)}
    sha = _sha256(path)[0]
    declared = VERIFIED_PRODUCER_PROBES.get(sha)
    if declared is None:
        return {"present": False, "reason": "fleet_probe_digest_unverified",
                "path": str(path.resolve()), "sha256": sha,
                "verified_roles": sorted(
                    (role.get("role"), role.get("schema"))
                    for role in VERIFIED_PRODUCER_PROBES.values())}
    return {"present": True, "verified": True, "path": str(path.resolve()),
            "sha256": sha, **declared}


@lru_cache(maxsize=32)
def _fleet_inventory(path_name: str, _stat: tuple[int, int]) -> dict[str, Any]:
    """Same-campaign inventory with schema check and reconciled duplicate hosts."""
    path = Path(path_name)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"present": False, "reason": "fleet_inventory_unreadable",
                "path": str(path)}
    raw_nodes = document.get("nodes")
    schema_ok = (isinstance(raw_nodes, list) and bool(document.get("generated"))
                 and all(isinstance(entry, dict) for entry in raw_nodes))
    if not schema_ok:
        return {"present": False, "reason": "fleet_inventory_schema_unverified",
                "path": str(path), "sha256": _sha256(path)[0]}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in raw_nodes:
        host = str(entry.get("node") or "")
        if not host:
            continue
        grouped[host].append({
            "host": host, "hostname": entry.get("hostname"),
            "utc": entry.get("utc"), "npu_count": entry.get("npu_count"),
            "reachable": entry.get("reachable"),
            "compute": entry.get("compute"),
            "compute_seen": entry.get("compute_seen"),
        })
    nodes: dict[str, dict[str, Any]] = {}
    duplicate_consistent: list[str] = []
    duplicate_conflicts: list[str] = []
    for host, entries in grouped.items():
        nodes[host] = entries[0]
        if len(entries) == 1:
            continue
        identities = {(str(item.get("hostname") or ""), item.get("utc"),
                       item.get("npu_count"), item.get("reachable"))
                      for item in entries}
        if len(identities) == 1:
            duplicate_consistent.append(host)
        else:
            duplicate_conflicts.append(host)
    return {"present": True, "path": str(path.resolve()),
            "sha256": _sha256(path)[0], "generated": document.get("generated"),
            "nodes": nodes, "schema_ok": True,
            "duplicate_consistent": sorted(duplicate_consistent),
            "duplicate_conflicts": sorted(duplicate_conflicts)}


def _hardware_for(case_dir: Path, host: str) -> dict[str, Any]:
    """Exact preflight SKU, else same-campaign inventory family with subtype unresolved."""
    preflight = _hardware(str((case_dir.parent.parent / "evidence" /
                               f"preflight_{case_dir.name}.json").resolve())).get(host, {})
    if preflight.get("hardware_key"):
        key = str(preflight["hardware_key"])
        subtype = key if "_" in key else None
        return {**preflight, "hardware_family": key.split("_")[0],
                "hardware_subtype": subtype,
                "subtype_status": "declared" if subtype else "unresolved",
                "hardware_basis": "preflight_npu_smi",
                "source": "preflight"}
    root = case_dir.parent.parent
    inventory_path = root / "evidence" / "fleet_inventory.json"
    probe_path = root / "bin" / "fleet_probe.py"
    if not inventory_path.is_file():
        return {"hardware_key": None, "hardware_family": None,
                "hardware_subtype": None, "subtype_status": "unresolved",
                "hardware_basis": "preflight_and_inventory_unavailable",
                "host": host}
    inv_stat = inventory_path.stat()
    inventory = _fleet_inventory(str(inventory_path.resolve()),
                                 (inv_stat.st_size, inv_stat.st_mtime_ns))
    node = (inventory.get("nodes") or {}).get(host)
    common = {"hardware_key": None, "hardware_family": None,
              "hardware_subtype": None, "subtype_status": "unresolved",
              "host": host,
              "inventory_path": inventory.get("path"),
              "inventory_sha256": inventory.get("sha256"),
              "inventory_generated": inventory.get("generated")}
    if not inventory.get("present"):
        return {**common, "hardware_basis": inventory.get("reason")}
    if host in (inventory.get("duplicate_conflicts") or ()):
        return {**common, "hardware_basis": "inventory_duplicate_host_conflict"}
    inventory_duplicate_consistent = host in (inventory.get("duplicate_consistent") or ())
    if node is None:
        return {**common, "hardware_basis": "host_not_in_inventory"}
    if node.get("reachable") is not True or node.get("npu_count") != 8:
        return {**common, "hardware_basis": "inventory_node_unreachable_or_count_not_8",
                "node": node}
    if not node.get("hostname") or not node.get("utc"):
        return {**common, "hardware_basis": "inventory_hostname_or_utc_missing",
                "node": node}
    status = _capture_status(str(case_dir.resolve()))
    case_epoch = _parse_utc(status.get("started"))
    inventory_epoch = _parse_utc(inventory.get("generated"))
    node_epoch = _parse_utc(node.get("utc"))
    if case_epoch is None or inventory_epoch is None or node_epoch is None:
        return {**common, "hardware_basis": "inventory_or_case_epoch_missing",
                "node": node}
    if not (case_epoch.date() == inventory_epoch.date() == node_epoch.date()):
        return {**common, "hardware_basis": "inventory_epoch_mismatch",
                "case_started": status.get("started"), "node": node}
    prepare_entries = [item for item in status.get("prepare") or ()
                       if isinstance(item, dict) and str(item.get("node")) == host]
    if not prepare_entries:
        return {**common, "hardware_basis": "host_not_in_prepare", "node": node}
    if len({str(item.get("hostname") or "") for item in prepare_entries}) > 1:
        return {**common, "hardware_basis": "prepare_duplicate_host_conflict",
                "node": node, "prepare_count": len(prepare_entries),
                "prepare_hostnames": sorted({str(item.get("hostname") or "")
                                             for item in prepare_entries})}
    if len({item.get("dies_visible") for item in prepare_entries}) > 1:
        return {**common, "hardware_basis": "prepare_duplicate_host_conflict",
                "node": node, "prepare_count": len(prepare_entries),
                "prepare_dies_visible": sorted(str(item.get("dies_visible"))
                                               for item in prepare_entries)}
    if len({str(item.get("model_path") or "") for item in prepare_entries}) > 1:
        return {**common, "hardware_basis": "prepare_duplicate_host_conflict",
                "node": node, "prepare_count": len(prepare_entries),
                "prepare_model_paths": sorted({str(item.get("model_path") or "")
                                               for item in prepare_entries})}
    prepare = prepare_entries[0]
    if str(prepare.get("hostname") or "") != str(node.get("hostname") or ""):
        return {**common, "hardware_basis": "inventory_prepare_hostname_conflict",
                "node": node, "prepare_hostname": prepare.get("hostname")}
    if prepare.get("dies_visible") is not None and prepare.get("dies_visible") != 8:
        return {**common, "hardware_basis": "prepare_dies_visible_not_8",
                "node": node, "prepare_dies_visible": prepare.get("dies_visible")}
    probe_stat = probe_path.stat() if probe_path.is_file() else None
    probe = (_fleet_probe(str(probe_path.resolve()),
                          (probe_stat.st_size, probe_stat.st_mtime_ns))
             if probe_stat is not None else {"present": False,
                                             "reason": "fleet_probe_missing"})
    if not probe.get("present"):
        return {**common, "hardware_basis": probe.get("reason", "fleet_probe_missing"),
                "node": node, "probe": probe}
    family = probe.get("family")
    if not family:
        return {**common, "hardware_basis": "fleet_probe_role_family_absent",
                "node": node, "probe": probe}
    return {
        **common,
        "hardware_key": family,
        "hardware_family": family,
        "hardware_subtype": None,
        "subtype_status": "unresolved",
        "hardware_basis": "same_campaign_fleet_inventory_probe_family",
        "source": "evidence/fleet_inventory.json",
        "hostname": node.get("hostname"),
        "npu_count": node.get("npu_count"),
        "inventory_utc": node.get("utc"),
        "inventory_generated": inventory.get("generated"),
        "inventory_sha256": inventory.get("sha256"),
        "probe_path": probe.get("path"),
        "probe_sha256": probe.get("sha256"),
        "probe_role": probe.get("role"),
        "probe_schema": probe.get("schema"),
        "probe_verified": True,
        "prepare_count": len(prepare_entries),
        "inventory_duplicate_consistent": inventory_duplicate_consistent,
        "node": node,
    }


def _worker_rank(declaration: LaunchDeclaration | None, device_id: int | None,
                 worker: str) -> tuple[int | None, str, str | None]:
    """Derive the global rank from launch x device; report conflicts explicitly."""
    if declaration is None:
        return None, "launch_declaration_unavailable", None
    if device_id is None:
        return None, "raw_device_id_unavailable", None
    if device_id >= declaration.dp_local * declaration.tp:
        return None, "device_id_outside_declared_local_workers", None
    rank = declaration.dp_start * declaration.tp + device_id
    conflict = None
    match = re.match(r"dp(\d+)_", worker)
    if match:
        label = int(match.group(1))
        expected = declaration.dp_start + device_id // declaration.tp
        if label != expected:
            conflict = f"worker_dp_label={label}!=launch_derived_dp={expected}"
    return rank, "launch_data_parallel_start_rank_x_tp_plus_raw_device_id", conflict


WEIGHT_CONFIG_ROOTS = (
    Path("/Volumes/data/mindie-sim-data/a5/weights-metadata-20261108"),
    Path("/Volumes/data/mindie-sim-data/a5/weights-catalog"),
)
_RECEIPT_LINE = re.compile(r"CELL\s+(\S+).*?export=\[(.*?)\]")
_EXPORT_ENTRY = re.compile(r"\(\s*'([^']+)'\s*,\s*(None|\d+)\s*\)")
_RANK_RECEIPT = re.compile(r"rank=(\S+?)/(\S+)\s+.*?gz=(\d+)")
_PROBE_SHA = re.compile(r"([0-9a-f]{64})\s+(\S*config\.json)")


def _decompressed_sha(path: Path) -> str | None:
    """True raw-stream identity: SHA-256 of the decompressed CSV bytes."""
    digest = hashlib.sha256()
    try:
        with gzip.open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError:
        return None
    return digest.hexdigest()


@lru_cache(maxsize=8)
def _weight_config_index(root_names: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """Index retained weight configs by their content SHA-256."""
    found: dict[str, dict[str, Any]] = {}
    for name in root_names:
        base = Path(name)
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*/config.json")):
            try:
                digest, size = _sha256(path)
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            found.setdefault(digest, {
                "sha256": digest, "size_bytes": size, "path": str(path.resolve()),
                "model_dir": path.parent.name, "config": document,
                "all_paths": [], "entries": []})
            found[digest]["all_paths"].append(str(path.resolve()))
            found[digest]["entries"].append({
                "path": str(path.resolve()), "model_dir": path.parent.name,
                "config": document})
    return found


@lru_cache(maxsize=32)
def _capture_status(case_dir_name: str) -> dict[str, Any]:
    path = Path(case_dir_name) / "status.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def deployment_metadata(spec: Any, raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """Attach the actual OCI image id/label from the original status.json.

    Only deployment identity is read: no target kernel_details, rank table or
    measured duration.  A missing/failed/foreign deployment leaves the case
    unchanged, so the producer remains explicitly unpinned.
    """
    source = getattr(spec, "source_case_dir", None)
    if source is None:
        return raw
    case_dir = Path(source)
    status = _capture_status(str(case_dir.resolve()))
    if not isinstance(status, dict) or str(status.get("status") or "").lower() in {
            "failed", "error", "invalid"}:
        return raw
    runtime = dict(raw.get("runtime") or {}) if isinstance(raw, Mapping) else {}
    meta = dict(runtime.get("metadata") or {})
    # Caller-supplied revision/id declarations win; the status digest fills
    # only an absent identity and overrides a conflicting label.
    if meta.get("mx_quant_source_revision") or any(
            meta.get(key) for key in ("image_id", "oci_image_digest",
                                      "deployment_image_id")):
        return raw
    declaration = status.get("spec") if isinstance(status.get("spec"), Mapping) else {}
    nodes = {str(item) for item in (declaration.get("nodes") or ()) if str(item)}
    prepare = [item for item in (status.get("prepare") or ())
               if isinstance(item, Mapping)]
    matched = [item for item in prepare
               if not nodes or str(item.get("node") or "") in nodes]
    if not matched or any(item.get("created") is not True for item in matched):
        return raw
    if nodes and nodes - {str(item.get("node") or "") for item in matched}:
        return raw
    ids = {str(item.get("image_id") or "") for item in matched}
    labels = {str(item.get("image") or "") for item in matched}
    if len(ids) != 1 or "" in ids:
        return raw
    label = str(declaration.get("image") or "")
    if label and labels and label not in labels:
        return raw
    # A successful prepare is deployment proof; capture existence/outcome is
    # not.  The same real image must bind before a cell is ever captured.
    meta["image_id"] = next(iter(ids))
    if not any(meta.get(key) for key in ("image", "oci_image", "deployment_image")):
        meta["image"] = label or next(iter(labels))
    runtime["metadata"] = meta
    return {**raw, "runtime": runtime}


@lru_cache(maxsize=64)
def _tarball_case_index(case_dir_name: str) -> dict[str, dict[str, list[tuple[str, int]]]]:
    """Package member index: cell -> host -> [(worker, gzip bytes)] from producer tarballs."""
    result: dict[str, dict[str, list[tuple[str, int]]]] = {}
    for archive in sorted(Path(case_dir_name).glob("*.tar.gz")):
        try:
            with tarfile.open(archive, "r:gz") as handle:
                for member in handle:
                    if not member.name.endswith("kernel_details.csv.gz"):
                        continue
                    parts = member.name.strip("/").split("/")
                    if len(parts) < 6 or parts[0] != "out":
                        continue
                    dirname, host, worker = parts[2], parts[3], parts[4]
                    cell = (dirname if dirname.startswith(Path(case_dir_name).name + "_")
                            else f"{Path(case_dir_name).name}_{dirname}")
                    result.setdefault(cell, {}).setdefault(host, []).append(
                        (worker, int(member.size)))
        except (OSError, tarfile.TarError):
            continue
    return result


@lru_cache(maxsize=64)
def _structured_receipts(case_dir_name: str) -> dict[str, list[dict[str, Any]]]:
    """Current export versions recorded in status.cells[].export (producer session)."""
    status = _capture_status(case_dir_name)
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in status.get("cells") or ():
        if not isinstance(cell, dict) or cell.get("captured") is not True:
            continue
        if cell.get("rc") not in (0, None):
            continue
        tag = cell.get("tag")
        if not tag:
            continue
        exports = cell.get("export")
        entries = (exports if isinstance(exports, list)
                   else [exports] if isinstance(exports, dict) else [])
        for item in entries:
            if not isinstance(item, dict) or item.get("ok") is not True:
                continue
            host = item.get("host") or item.get("node")
            worker = item.get("rank")
            rank_dir = item.get("rank_dir") or item.get("exported") or ""
            parts = Path(str(rank_dir)).parts
            if not worker and len(parts) >= 2:
                worker, host = parts[-1], parts[-2]
            size = (item.get("kernel_gz_bytes") or item.get("gz_bytes")
                    or (item.get("files") or {}).get("kernel_details.csv.gz"))
            if not host or str(host) == str(cell.get("name")):
                continue
            if not worker or size is None:
                continue
            result[str(tag)].append({
                "cell_id": str(tag), "host": str(host), "worker": str(worker),
                "size_bytes": int(size), "source": "status.cells.export",
                "session_started": cell.get("started"),
                "session_finished": cell.get("finished"),
                "session_epoch": cell.get("started_epoch"),
            })
    return dict(result)


@lru_cache(maxsize=64)
def _case_receipts(case_dir_name: str, root_names: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """Merge structured current exports, log sessions and tarball canonical members."""
    case_dir = Path(case_dir_name)
    prefix = case_dir.name + "_"
    logs = {cell: record for cell, record in _receipt_index(root_names).items()
            if cell.startswith(prefix)}
    structured = _structured_receipts(case_dir_name)
    tarballs = _tarball_case_index(case_dir_name)

    def resolve(entries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        resolved = []
        for entry in entries:
            item = dict(entry)
            if not item.get("worker"):
                matches = [worker for worker, size in
                           tarballs.get(item["cell_id"], {}).get(item["host"], [])
                           if size == item.get("size_bytes")]
                if len(matches) == 1:
                    item["worker"] = matches[0]
                    item["worker_source"] = "tarball_member_exact_size"
                elif len(matches) > 1:
                    item["worker_ambiguous"] = sorted(matches)
            resolved.append(item)
        return resolved

    result: dict[str, dict[str, Any]] = {}
    for cell in sorted(set(logs) | set(structured)):
        record = logs.get(cell) or {"current": [], "history": []}
        current = [{**entry, "cell_id": cell} for entry in structured.get(cell, [])]
        history = [resolve([{**entry, "cell_id": cell} for entry in group])
                   for group in record.get("history", [])]
        log_current = resolve([{**entry, "cell_id": cell}
                               for entry in record.get("current", [])])
        for entry in log_current:
            same_host_structured = [item for item in current
                                    if item.get("host") == entry.get("host")]
            if same_host_structured:
                duplicate = any(item.get("worker") == entry.get("worker")
                                and item.get("size_bytes") == entry.get("size_bytes")
                                for item in same_host_structured)
                if not duplicate:
                    history.append([entry])
                continue
            current.append(entry)
        canonical = [{"cell_id": cell, "host": host, "worker": worker,
                      "size_bytes": size, "source": "tarball_member"}
                     for host, members in tarballs.get(cell, {}).items()
                     for worker, size in members]
        seen = set()
        deduped = []
        for group in history:
            key = tuple(sorted((item.get("host"), item.get("worker"),
                                item.get("size_bytes")) for item in group))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(group)
        history = deduped
        result[cell] = {"current": current, "history": history,
                        "canonical": canonical,
                        "receipt_source": ("structured_status_cells"
                                           if structured.get(cell) else "producer_logs")}
    return result


@lru_cache(maxsize=8)
def _receipt_index(root_names: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """Producer receipts: the last ``CELL ... export=[(host,size),...]`` wins."""
    receipts: dict[str, dict[str, Any]] = {}
    for name in root_names:
        base = Path(name)
        if not base.is_dir():
            continue
        for log in sorted((*base.glob("logs/*.log"), *base.glob("out/*/logs/*.log"))):
            try:
                text = log.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                match = _RECEIPT_LINE.search(line)
                if match:
                    cell_id = match.group(1)
                    exports = [{"host": host, "worker": None,
                                "size_bytes": None if size == "None" else int(size)}
                               for host, size in _EXPORT_ENTRY.findall(match.group(2))]
                else:
                    rank = _RANK_RECEIPT.search(line)
                    cell = re.search(r"CELL\s+(\S+)", line)
                    if rank is None or cell is None:
                        continue
                    cell_id = cell.group(1)
                    exports = [{"host": rank.group(1), "worker": rank.group(2),
                                "size_bytes": int(rank.group(3))}]
                record = receipts.setdefault(cell_id, {"history": [], "current": []})
                record["history"].append(exports)
                record["current"] = exports
    return receipts


def _probe_receipt(prepare: Mapping[str, Any]) -> tuple[str | None, str | None]:
    """Return (config_path, config_sha256) from status.prepare[].model_probe[]."""
    probe = prepare.get("model_probe")
    if not isinstance(probe, list):
        return None, None
    config_path = str(probe[0]) if probe and isinstance(probe[0], str) else None
    for item in probe:
        if not isinstance(item, str):
            continue
        match = _PROBE_SHA.search(item)
        if match:
            return match.group(2) or config_path, match.group(1)
    return config_path, None


def _select_weight_entry(entries: Sequence[Mapping[str, Any]], launch_model_dir: str | None,
                         launch_config_path: str | None) -> tuple[Mapping[str, Any] | None,
                                                                  str | None]:
    if not entries:
        return None, "weight_config_sha_not_retained"
    if len(entries) == 1:
        return entries[0], None
    launch_name = Path(str(launch_model_dir or "")).name
    for entry in entries:
        if entry.get("model_dir") == launch_name:
            return entry, None
    launch_path = Path(str(launch_config_path or ""))
    if launch_path.name:
        for entry in entries:
            if Path(str(entry.get("path"))).parent.name == launch_path.parent.name:
                return entry, None
    geometry = set()
    for entry in entries:
        config = entry.get("config") or {}
        geometry.add((config.get("num_hidden_layers"), config.get("hidden_size"),
                      config.get("vocab_size")))
    if len(geometry) == 1:
        return entries[0], "same_sha_multiple_deployments_geometry_identical"
    return None, "config_sha_geometry_conflict"


def _actual_model_binding(case_dir: Path, host: str, tp: int
                          ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None,
                                     str | None, Mapping[str, Any]]:
    """Bind the deployed model from the rank host's own preflight/prepare declaration."""
    status = _capture_status(str(case_dir.resolve()))
    spec = status.get("spec") if isinstance(status.get("spec"), dict) else {}
    spec_source = "capture_status"
    if not spec.get("model"):
        case_json = case_dir.parent.parent / "cases" / f"{case_dir.name}.json"
        if case_json.is_file():
            try:
                spec = json.loads(case_json.read_text(encoding="utf-8"))
                spec_source = str(case_json)
            except (OSError, ValueError):
                spec = {}
    preflight = status.get("preflight") if isinstance(status.get("preflight"), list) else []
    prepare = status.get("prepare") if isinstance(status.get("prepare"), list) else []
    evidence: dict[str, Any] = {
        "host": host,
        "launch_model_dir": spec.get("model"),
        "quantization": spec.get("quantization"),
        "served": spec.get("served"),
        "status_started": status.get("started"),
        "launch_model_source": spec_source,
        "basis": "capture_declaration_unavailable",
    }
    preflight_entry = next((item for item in preflight
                            if isinstance(item, dict) and str(item.get("node")) == host), None)
    prepare_entry = next((item for item in prepare
                          if isinstance(item, dict) and str(item.get("node")) == host), None)
    cfg_sha: str | None = None
    launch_config_path: str | None = None
    if preflight_entry is not None:
        cfg_sha = str(preflight_entry.get("cfg") or "") or None
        evidence["basis"] = "capture_status_preflight_cfg"
        evidence["declaration_source"] = "preflight"
    elif prepare_entry is not None:
        launch_config_path, cfg_sha = _probe_receipt(prepare_entry)
        evidence["basis"] = "capture_status_prepare_model_probe"
        evidence["declaration_source"] = "prepare"
        if prepare_entry.get("model_path"):
            evidence["launch_model_dir"] = prepare_entry.get("model_path")
    elif preflight:
        evidence["basis"] = "host_not_in_preflight"
    elif prepare:
        evidence["basis"] = "host_not_in_prepare"
    evidence["preflight_cfg_sha256"] = cfg_sha
    evidence["launch_config_path"] = launch_config_path
    if not cfg_sha:
        return None, None, str(evidence["basis"]), evidence
    index = _weight_config_index(tuple(str(path.resolve()) for path in WEIGHT_CONFIG_ROOTS))
    matched = index.get(cfg_sha)
    if matched is None:
        return None, None, f"weight_config_sha_not_retained:{cfg_sha}", evidence
    entry, select_note = _select_weight_entry(
        matched.get("entries") or [], evidence.get("launch_model_dir"), launch_config_path)
    if entry is None:
        return None, None, str(select_note), evidence
    from mindie_sim.catalog.specs import build_model_spec
    try:
        model = build_model_spec(entry["model_dir"], entry["config"])
        config = model.to_dict()
    except (ValueError, KeyError, TypeError) as exc:
        return None, None, f"weight_config_unparsed:{type(exc).__name__}:{exc}", evidence
    config["tp"] = tp
    raw_case = {
        "model": {"hf_config": entry["config"]},
        "machine": {"backend": "ascend", "sku": "Ascend950DT_9582",
                    "num_devices": 8, "ranks_per_node": 8},
        "workload": {"requests": [{"id": "native", "prompt_tokens": 1,
                                   "output_tokens": 1}]},
        "runtime": {"tp": tp, "dp": 1, "ep": 1, "pp": 1},
    }
    evidence.update({
        "weight_config_sha256": cfg_sha,
        "weight_config_path": entry["path"],
        "weight_config_paths": matched["all_paths"],
        "weight_model_dir": entry["model_dir"],
        "architecture": (entry["config"].get("architectures") or [None])[0],
        "layers": config.get("layers"), "hidden_size": config.get("hidden_size"),
        "vocab_size": config.get("vocab_size"), "tp": tp,
        "selection_note": select_note,
        "identity_basis": "launch_model_dir_and_weight_config_sha",
    })
    return raw_case, config, None, evidence


def _terminal_receipt_index(value: Any) -> dict[str, list[dict[str, Any]]] | None:
    """Accept caller-supplied producer terminal receipts (mapping/JSONL/TSV)."""
    if value is None:
        return None
    if isinstance(value, (str, Path)):
        path = Path(value)
        rows = []
        opener = gzip.open if path.name.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    else:
        rows = list(value)
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        cell = item.get("cell_id") or item.get("cell")
        host = item.get("host")
        size = item.get("size_bytes", item.get("size"))
        if not cell or not host or size is None:
            continue
        result[str(cell)].append({
            "host": str(host), "worker": item.get("worker"),
            "size_bytes": int(size), "cell_id": str(cell),
            "worker_source": item.get("worker_source", "caller_terminal_receipt")})
    return dict(result)


def _receipt_match(entries: Sequence[Mapping[str, Any]], host: str, worker: str,
                   size: int) -> Mapping[str, Any] | None:
    for entry in entries:
        if entry.get("host") != host or entry.get("size_bytes") != size:
            continue
        expected_worker = entry.get("worker")
        if expected_worker and expected_worker != worker:
            continue
        return entry
    return None


def _source_classification(source: "CellSource", path: Path, size: int,
                           stream_sha: str | None, host: str, worker: str,
                           root_names: tuple[str, ...],
                           terminal_receipts: Mapping[str, list[dict[str, Any]]] | None = None
                           ) -> tuple[str, Mapping[str, Any]]:
    """Classify a retained rank export with versioned producer receipts.

    Identity is anchored to the retained host/worker/bytes path.  A receipt
    version is chosen by exact host/worker/bytes match, never by latest log
    size or largest size.  Structured ``status.cells[].export`` versions are
    current; earlier log/tarball versions remain history.  A worker absent
    from independent receipts is host+size association only, explicitly
    unverified; a contradictory supplied worker is rejected before matching.
    """
    cell_id = _cell_id(source.case_dir, source.cell_dir)
    evidence: dict[str, Any] = {
        "raw_stream_sha256": stream_sha, "compressed_sha256": None,
        "compressed_size": size, "host": host, "worker": worker,
        "producer_receipt": None, "receipt_match": "receipt_unavailable",
        "receipt_source": None, "source_grade": None, "exact_identity": False,
        "worker_qualification": "unverified",
        "independent_source_key": stream_sha or f"{cell_id}:{host}:{worker}",
    }
    retained_ranks = [{"host": item.parent.parent.name, "worker": item.parent.name,
                       "size_bytes": item.stat().st_size} for item in source.traces]
    evidence["retained_ranks"] = retained_ranks
    evidence["rank_count_retained"] = len(retained_ranks)
    # Path identity is the opaque original: a copied/renamed path or a
    # contradictory host/worker argument cannot inherit another trace's receipt.
    retained_paths = {item.resolve() for item in source.traces}
    if path.resolve() not in retained_paths:
        evidence.update({"source_class": "invalid_source_path",
                         "receipt_match": "path_not_in_retained_cell"})
        return "invalid_source_path", evidence
    path_host, path_worker = path.parent.parent.name, path.parent.name
    if host != path_host or worker != path_worker:
        evidence.update({
            "source_class": "host_not_in_receipt" if host != path_host else "extra_trace",
            "receipt_match": "path_host_conflict" if host != path_host else "path_worker_conflict",
            "worker_qualification": "path_conflict",
            "retained_path": str(path.resolve()),
        })
        return str(evidence["source_class"]), evidence

    if terminal_receipts is not None:
        base = _case_receipts(str(source.case_dir.resolve()), root_names).get(cell_id) or {}
        receipts = {
            "current": [dict(entry) for entry in terminal_receipts.get(cell_id, [])],
            "history": list(base.get("history", [])),
            "canonical": list(base.get("canonical", [])),
            "receipt_source": "caller_terminal_receipts",
        }
    else:
        receipts = _case_receipts(str(source.case_dir.resolve()),
                                  root_names).get(cell_id)
    if not receipts:
        evidence["source_class"] = "receipt_unavailable"
        return "receipt_unavailable", evidence
    current = [item for item in receipts.get("current", [])
               if item.get("size_bytes") is not None]
    history = [[item for item in group if item.get("size_bytes") is not None]
               for group in receipts.get("history", [])]
    canonical = [item for item in receipts.get("canonical", [])
                 if item.get("size_bytes") is not None]
    evidence.update({
        "producer_receipt": current,
        "receipt_history": history,
        "canonical_members": canonical,
        "receipt_source": receipts.get("receipt_source"),
        "rank_count_receipt": len(current),
        "receipt_scope": ("host_worker_size" if any(item.get("worker") for item in current)
                          else "host_size"),
    })
    missing = [item for item in current
               if not any(item["host"] == rank["host"]
                          and (not item.get("worker") or item["worker"] == rank["worker"])
                          and item["size_bytes"] == rank["size_bytes"]
                          for rank in retained_ranks)]
    evidence["missing_receipt_ranks"] = missing

    def exact_versions(entries):
        for entry in entries:
            if (entry.get("host") == host and entry.get("size_bytes") == size
                    and entry.get("worker") == worker):
                yield entry

    def history_versions(entries):
        for entry in entries:
            if (entry.get("host") == host and entry.get("size_bytes") == size
                    and (not entry.get("worker") or entry.get("worker") == worker)):
                yield entry

    exact_current = next(exact_versions(current), None)
    exact_history = next(history_versions([item for group in history for item in group]), None)
    exact_canonical = next(exact_versions(canonical), None)
    host_size_current = next((entry for entry in current
                              if entry.get("host") == host
                              and entry.get("size_bytes") == size
                              and not entry.get("worker")), None)
    if exact_current is not None:
        from_tarball = exact_current.get("worker_source") == "tarball_member_exact_size"
        source_class = "actual"
        evidence.update({
            "receipt_match": "current",
            "source_grade": ("B_canonical_path_identity" if from_tarball
                             else "A_independent_producer_receipt"),
            "worker_qualification": ("canonical_path_identity" if from_tarball
                                     else "exact_independent_receipt"),
            "exact_identity": True,
            "matched_version": exact_current})
    elif host_size_current is not None:
        source_class = "actual"
        evidence["receipt_match"] = "current_host_size_only"
        if exact_canonical is not None:
            evidence.update({"source_grade": "B_canonical_path_identity",
                             "worker_qualification": "canonical_path_identity",
                             "exact_identity": True,
                             "matched_version": exact_canonical})
        else:
            evidence.update({"source_grade": "C_host_size_association",
                             "worker_qualification": "host_size_only_unverified",
                             "exact_identity": False,
                             "matched_version": host_size_current})
    elif exact_history is not None:
        source_class = "stale_superseded"
        evidence.update({"receipt_match": "earlier",
                         "source_grade": "A_independent_producer_receipt",
                         "worker_qualification": "exact_independent_receipt",
                         "matched_version": exact_history})
    elif exact_canonical is not None:
        source_class = "canonical_path_only"
        evidence.update({"receipt_match": "canonical_only",
                         "source_grade": "B_canonical_path_identity",
                         "worker_qualification": "canonical_path_identity",
                         "exact_identity": True,
                         "matched_version": exact_canonical})
    elif any(item.get("host") == host for item in current):
        source_class = "extra_trace"
        evidence["receipt_match"] = "host_present_size_absent"
    elif any(item.get("host") == host for group in history for item in group):
        source_class = "extra_trace"
        evidence["receipt_match"] = "host_present_in_history"
    elif any(item.get("host") == host for item in canonical):
        source_class = "host_not_in_receipt"
        evidence["receipt_match"] = "canonical_member_only"
    else:
        source_class = "host_not_in_receipt"
        evidence["receipt_match"] = "host_absent"
    # Shared physical payload: same host+worker export retained under another ID.
    peers = []
    for other_id, sources in _index(root_names).items():
        if other_id == cell_id:
            continue
        for other in sources:
            for peer in other.traces:
                if peer.parent.parent.name == host and peer.parent.name == worker:
                    peers.append({"cell_id": other_id, "path": str(peer),
                                  "host": host, "worker": worker})
    shared = []
    for peer in peers:
        peer_sha = _decompressed_sha(Path(peer["path"]))
        peer["raw_stream_sha256"] = peer_sha
        if peer_sha and stream_sha and peer_sha == stream_sha:
            shared.append(peer)
    if shared and source_class in {"actual", "canonical_path_only"}:
        source_class = "shared_payload"
        evidence["shared_with"] = shared
        evidence["independent_source_key"] = stream_sha
    evidence["source_class"] = source_class
    return source_class, evidence



# ---------------------------------------------------------------------------
# Raw streaming measurement
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OperatorCell:
    op_type: str
    core: str
    count: int
    additive_ms: float
    min_ms: float | None
    max_ms: float | None
    start_ns: int | None
    end_ns: int | None
    source: str


@dataclass(frozen=True)
class StreamSpan:
    stream_id: str
    count: int
    additive_ms: float
    span_ms: float | None
    start_ns: int | None
    end_ns: int | None


@dataclass
class _Scan:
    rows: int = 0
    positive: int = 0
    bad_rows: int = 0
    first_start_ns: int | None = None
    last_end_ns: int | None = None
    additive_ns: int = 0
    device_ids: set[str] = field(default_factory=set)
    operators: dict[tuple[str, str], list[Any]] = field(default_factory=dict)
    streams: dict[str, list[Any]] = field(default_factory=dict)
    complete: bool = True

    def observe(self, event: Any) -> None:
        self.positive += 1
        self.device_ids.add(str(event.device_id))
        self.first_start_ns = event.start_ns if self.first_start_ns is None else min(self.first_start_ns, event.start_ns)
        self.last_end_ns = event.end_ns if self.last_end_ns is None else max(self.last_end_ns, event.end_ns)
        self.additive_ns += event.duration_ns
        key = (str(event.op_type or ""), str(event.core or ""))
        cell = self.operators.get(key)
        if cell is None:
            self.operators[key] = [1, event.duration_ns, event.duration_ns, event.duration_ns,
                                   event.start_ns, event.end_ns]
        else:
            cell[0] += 1
            cell[1] += event.duration_ns
            cell[2] = min(cell[2], event.duration_ns)
            cell[3] = max(cell[3], event.duration_ns)
            cell[4] = min(cell[4], event.start_ns)
            cell[5] = max(cell[5], event.end_ns)
        stream = self.streams.get(str(event.stream_id))
        if stream is None:
            self.streams[str(event.stream_id)] = [1, event.duration_ns, event.start_ns, event.end_ns]
        else:
            stream[0] += 1
            stream[1] += event.duration_ns
            stream[2] = min(stream[2], event.start_ns)
            stream[3] = max(stream[3], event.end_ns)

    @property
    def span_ms(self) -> float | None:
        if self.first_start_ns is None or self.last_end_ns is None:
            return None
        return (self.last_end_ns - self.first_start_ns) / 1e6

    @property
    def additive_ms(self) -> float:
        return self.additive_ns / 1e6

    def operator_cells(self) -> tuple[OperatorCell, ...]:
        return tuple(
            OperatorCell(
                op_type=op_type, core=core, count=int(value[0]),
                additive_ms=value[1] / 1e6, min_ms=value[2] / 1e6,
                max_ms=value[3] / 1e6, start_ns=value[4], end_ns=value[5],
                source="kernel_details.csv")
            for (op_type, core), value in sorted(self.operators.items()))

    def stream_spans(self) -> tuple[StreamSpan, ...]:
        return tuple(
            StreamSpan(
                stream_id=stream, count=int(value[0]),
                additive_ms=value[1] / 1e6,
                span_ms=(value[3] - value[2]) / 1e6,
                start_ns=value[2], end_ns=value[3])
            for stream, value in sorted(self.streams.items()))


def _scan_only(path: Path, *, rank_id: str, max_rows: int,
               timeout_s: float) -> tuple[_Scan, Any]:
    schema = probe_csv(path)
    scan = _Scan()
    source = CsvSource(schema, rank_id=rank_id, rank_index=None)
    for event in source.iter_events(max_rows=max_rows, timeout_s=timeout_s):
        scan.rows += 1
        scan.observe(event)
    return scan, schema


def _safe_scan(path: Path, *, rank_id: str, max_rows: int,
               timeout_s: float) -> tuple[_Scan, Any, str | None]:
    try:
        scan, schema = _scan_only(path, rank_id=rank_id, max_rows=max_rows,
                                  timeout_s=timeout_s)
        return scan, schema, None
    except (OSError, ValueError, KeyError, ProfilerSchemaError, ProfilerQueryError) as exc:
        return _Scan(complete=False), None, f"{type(exc).__name__}:{exc}"


def _decode_timetable(path: Path, config: Mapping[str, Any], source: SourceRef,
                      *, rank_id: str, max_rows: int,
                      timeout_s: float) -> tuple[_Scan, Any, dict[str, Any]]:
    """One scan: aggregate raw evidence while the segmenter consumes events."""
    schema = probe_csv(path)
    scan = _Scan()
    csv_source = CsvSource(schema, rank_id=rank_id, rank_index=None)

    def events():
        for event in csv_source.iter_events(max_rows=max_rows, timeout_s=timeout_s):
            scan.rows += 1
            scan.observe(event)
            yield event

    report = auto_segment_decode_forwards(
        events(), config, source=source, max_events=max_rows,
        max_forwards=_MAX_FORWARDS,
        max_detailed_forwards=_MAX_FORWARD_SAMPLES,
        max_samples_per_layer=0, max_anomalies=50)
    return scan, schema, report


# ---------------------------------------------------------------------------
# Maintained prefill extraction boundary
# ---------------------------------------------------------------------------

def _prefill_observation(raw: Mapping[str, Any], path: Path, *,
                         max_rows: int, timeout_s: float):
    from scoped_native_replay import extract_full_observation
    return extract_full_observation(raw, path, max_rows=max_rows, timeout_s=timeout_s)


# ---------------------------------------------------------------------------
# Model declaration
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=64)
def _model_declaration(model_case: str, _stat: tuple[int, int]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    from mindie_sim.prediction.structure import parse_case
    path = Path(model_case)
    raw = json.loads(path.read_text(encoding="utf-8"))
    case = parse_case(raw)
    config = case.model.to_dict()
    return raw, config


_DECLARATION_KEYS = (
    "name", "layers", "body_layers", "hidden_size", "vocab_size",
    "num_heads", "num_kv_heads", "head_dim", "intermediate_size",
    "moe_intermediate_size", "num_experts", "num_shared_experts", "top_k",
    "tp", "layer_plans", "source_attention_anchors", "source_decode_query",
    "forward_closure", "sequence_parallel", "auxiliary", "max_decode_query",
)
_ANCHOR_INPUTS = ("source_attention_anchors", "source_decode_query",
                  "forward_closure")


@lru_cache(maxsize=128)
def _file_sha(path: str, _stat: tuple[int, int]) -> str:
    return _sha256(Path(path))[0]


def _sanitize_declaration(config: Mapping[str, Any], *, tp: int) -> dict[str, Any]:
    """Keep only structural simulation inputs; measurement payloads are dropped."""
    clean = {key: config[key] for key in _DECLARATION_KEYS if key in config}
    clean["tp"] = tp
    if not clean.get("layer_plans"):
        raise ValueError("declaration_requires_layer_plans")
    if not clean.get("hidden_size") or not clean.get("vocab_size"):
        raise ValueError("declaration_requires_hidden_and_vocab")
    return clean


def _declaration_from_path(path: Path, *, tp: int) -> tuple[Mapping[str, Any] | None,
                                                            Mapping[str, Any], str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(document.get("layer_plans"), list):
        return None, _sanitize_declaration(document, tp=tp), "declared_model_config"
    from mindie_sim.prediction.structure import parse_case
    case = parse_case(document)
    config = case.model.to_dict()
    return document, _sanitize_declaration(config, tp=tp), "declared_case"


def _declared_config(declaration: Mapping[str, Any] | str | Path | None, tp: int
                     ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None,
                                str | None, Mapping[str, Any]]:
    """Parse an explicit structural declaration; measurement keys are dropped."""
    if declaration is None:
        return None, None, None, {}
    if not isinstance(declaration, (Mapping, str, Path)):
        to_dict = getattr(declaration, "to_dict", None)
        declaration = to_dict() if callable(to_dict) else declaration
    if declaration is None:
        return None, None, "declaration_not_mapping", {}
    try:
        if isinstance(declaration, Mapping):
            if isinstance(declaration.get("layer_plans"), list):
                raw, config, kind = None, _sanitize_declaration(declaration, tp=tp), "caller_mapping"
            else:
                from mindie_sim.prediction.structure import parse_case
                case = parse_case(dict(declaration))
                raw, config, kind = (declaration,
                                     _sanitize_declaration(case.model.to_dict(), tp=tp),
                                     "caller_case_mapping")
            sha = hashlib.sha256(json.dumps(declaration, sort_keys=True,
                                            default=str).encode()).hexdigest()
            origin = "caller_declaration"
        else:
            path = Path(str(declaration))
            if not path.is_absolute():
                path = _repo_root() / path
            if not path.is_file():
                return None, None, f"declaration_missing:{path}", {}
            stat = path.stat()
            raw, config, kind = _declaration_from_path(path, tp=tp)
            sha = _file_sha(str(path), (stat.st_size, stat.st_mtime_ns))
            origin = str(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return None, None, f"declaration_unparsed:{type(exc).__name__}:{exc}", {}
    return raw, config, None, {
        "origin": origin, "kind": kind, "sha256": sha,
        "basis": "explicit_structural_declaration_without_measurements",
        "declared_inputs": [key for key in _ANCHOR_INPUTS if key in config],
    }


def _model_config(row: Mapping[str, Any], case_dir: Path, host: str,
                  declaration: Mapping[str, Any] | str | Path | None = None
                  ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None,
                             str | None, Mapping[str, Any]]:
    """Resolve the deployed model from the capture preflight cfg, never a name template.

    Precedence:
      1. capture ``status.preflight[].cfg`` -> retained weight ``config.json``
         (exact content SHA).  Geometry/layers come from that config; the
         launch ``spec.model`` directory is retained as the quant namespace.
      2. an explicit structural ``declaration`` may overlay only the native
         anchor/query/closure inputs; it never replaces the bound geometry.
      3. if neither is available, return an explicit binding error.  The
         enrolled ``model_case`` catalog label is not used as a fallback.
    """
    tp = int(row.get("tp") or 1)
    raw_case, actual, binding_error, binding = _actual_model_binding(case_dir, host, tp)
    declared_raw, declared, declared_error, declared_prov = _declared_config(declaration, tp)
    if actual is not None:
        config = dict(actual)
        overlay = {}
        if declared is not None:
            for key in _ANCHOR_INPUTS + ("sequence_parallel",):
                if key in declared:
                    config[key] = declared[key]
                    overlay[key] = declared[key]
        provenance = {
            **binding,
            "actual_config_sha256": binding.get("weight_config_sha256"),
            "declaration": declared_prov or None,
            "declaration_error": declared_error,
            "declared_overlay_inputs": sorted(overlay),
            "raw_case_basis": "synthetic_case_from_bound_weight_config",
        }
        return raw_case, _sanitize_declaration(config, tp=tp), None, provenance
    if declared is not None:
        provenance = {
            **(declared_prov or {}),
            "actual_binding_error": binding_error,
            "actual_binding": binding,
            "basis": "explicit_structural_declaration_without_actual_capture_binding",
        }
        return declared_raw, declared, None, provenance
    provenance = {
        "actual_binding_error": binding_error,
        "actual_binding": binding,
        "declaration_error": declared_error,
        "basis": "actual_capture_binding_unavailable_no_template_fallback",
    }
    errors = [value for value in (binding_error, declared_error) if value]
    return None, None, ";".join(errors) or "model_binding_unavailable", provenance


# ---------------------------------------------------------------------------
# Published records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ForwardMeasurement:
    forward_id: str
    status: str
    start_ns: int | None
    end_ns: int | None
    span_ms: float | None
    activity_ms: float | None
    internal_gap_ms: float | None
    head_start_ns: int | None
    head_end_ns: int | None
    query_rows: int | None
    sequences_per_replica: int | None
    tokens_per_sequence: int | None
    layer_count: int | None
    basis: str


@dataclass(frozen=True)
class LayerMeasurement:
    forward_id: str
    layer_id: int
    start_ns: int | None
    end_ns: int | None
    span_ms: float
    activity_ms: float | None
    internal_gap_ms: float | None
    attention: str | None
    kind: str
    identity_status: str


@dataclass(frozen=True)
class LayerAggregate:
    layer_id: int
    count: int
    mean_ms: float | None
    p50_ms: float | None
    min_ms: float | None
    max_ms: float | None
    activity_mean_ms: float | None
    gap_mean_ms: float | None
    per_stream: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class TraceTimetable:
    cell_id: str
    phase: str
    trace_key: str
    source_path: str
    source_sha256: str
    raw_stream_sha256: str | None
    size_bytes: int
    source_class: str
    source_evidence: Mapping[str, Any]
    model_binding: Mapping[str, Any]
    header_sha256: str | None
    schema_version: str
    schema_variant: str
    optional_missing: tuple[str, ...]
    host: str
    worker: str
    rank: int | None
    device_id: int | None
    rank_basis: str
    rank_conflict: str | None
    hardware: Mapping[str, Any]
    hardware_basis: str
    launch: Mapping[str, Any]
    status: str
    reason: str | None
    raw_start_ns: int | None
    raw_end_ns: int | None
    raw_span_ms: float | None
    raw_additive_ms: float
    streams: tuple[StreamSpan, ...]
    operators: tuple[OperatorCell, ...]
    opstat_sha256: str | None
    opstat_device_ids: tuple[str, ...]
    opstat_status: str
    forwards: tuple[ForwardMeasurement, ...]
    layer_windows: tuple[LayerMeasurement, ...]
    layer_aggregates: tuple[LayerAggregate, ...]
    scan_counts: Mapping[str, Any]
    boundaries: Mapping[str, bool]
    declaration: Mapping[str, Any]
    limitations: tuple[str, ...]

    @property
    def source_grade(self) -> str | None:
        return self.source_evidence.get("source_grade")

    @property
    def exact_identity(self) -> bool:
        return self.source_evidence.get("exact_identity") is True

    @property
    def worker_qualification(self) -> str | None:
        return self.source_evidence.get("worker_qualification")

    @property
    def hardware_family(self) -> str | None:
        return self.hardware.get("hardware_family")

    @property
    def hardware_subtype(self) -> str | None:
        return self.hardware.get("hardware_subtype")

    def targets(self) -> Iterator["NativeTarget"]:
        detail = {
            "header_sha256": self.header_sha256,
            "raw_stream_sha256": self.raw_stream_sha256,
            "source_class": self.source_class,
            "source_evidence": dict(self.source_evidence),
            "model_binding": dict(self.model_binding),
            "raw_start_ns": self.raw_start_ns, "raw_end_ns": self.raw_end_ns,
            "schema_version": self.schema_version,
            "schema_variant": self.schema_variant,
            "optional_missing": self.optional_missing,
            "stream_additive_ms": tuple((item.stream_id, item.additive_ms) for item in self.streams),
            "opstat_sha256": self.opstat_sha256,
            "opstat_device_ids": self.opstat_device_ids,
            "boundaries": dict(self.boundaries),
            "limitations": self.limitations,
            "launch": dict(self.launch),
            "declaration": dict(self.declaration),
            "scan_counts": dict(self.scan_counts),
        }
        yield NativeTarget(
            key=self.trace_key, kind="trace", status=self.status,
            cell_id=self.cell_id, phase=self.phase, trace_key=self.trace_key,
            rank=self.rank, device_id=self.device_id, hardware=self.hardware,
            host=self.host, source_path=self.source_path,
            source_sha256=self.source_sha256, size_bytes=self.size_bytes,
            parent_key=None, start_ns=self.raw_start_ns, end_ns=self.raw_end_ns,
            value_ms=self.raw_span_ms, count=len(self.forwards),
            op_type=None, core=None, forward_id=None, layer_id=None,
            reason=self.reason, detail=detail)
        for cell in self.operators:
            yield NativeTarget(
                key=f"{self.trace_key}#op/{cell.op_type}|{cell.core}", kind="operator",
                status="measured", cell_id=self.cell_id, phase=self.phase,
                trace_key=self.trace_key, rank=self.rank, device_id=self.device_id,
                hardware=self.hardware, host=self.host, source_path=self.source_path,
                source_sha256=self.source_sha256, size_bytes=self.size_bytes,
                parent_key=self.trace_key, start_ns=cell.start_ns, end_ns=cell.end_ns,
                value_ms=cell.additive_ms, count=cell.count, op_type=cell.op_type,
                core=cell.core, forward_id=None, layer_id=None, reason=None,
                detail={"min_ms": cell.min_ms, "max_ms": cell.max_ms,
                        "source": cell.source})
        for forward in self.forwards:
            yield NativeTarget(
                key=f"{self.trace_key}#{forward.forward_id}", kind="forward",
                status=forward.status, cell_id=self.cell_id, phase=self.phase,
                trace_key=self.trace_key, rank=self.rank, device_id=self.device_id,
                hardware=self.hardware, host=self.host, source_path=self.source_path,
                source_sha256=self.source_sha256, size_bytes=self.size_bytes,
                parent_key=self.trace_key, start_ns=forward.start_ns,
                end_ns=forward.end_ns, value_ms=forward.span_ms, count=None,
                op_type=None, core=None, forward_id=forward.forward_id, layer_id=None,
                reason=None if forward.status == "measured" else forward.status,
                detail={"activity_ms": forward.activity_ms,
                        "internal_gap_ms": forward.internal_gap_ms,
                        "query_rows": forward.query_rows,
                        "sequences_per_replica": forward.sequences_per_replica,
                        "tokens_per_sequence": forward.tokens_per_sequence,
                        "layer_count": forward.layer_count, "basis": forward.basis})
            if forward.head_start_ns is not None and forward.head_end_ns is not None:
                head_ms = (forward.head_end_ns - forward.head_start_ns) / 1e6
                yield NativeTarget(
                    key=f"{self.trace_key}#{forward.forward_id}#head", kind="head",
                    status="measured", cell_id=self.cell_id, phase=self.phase,
                    trace_key=self.trace_key, rank=self.rank, device_id=self.device_id,
                    hardware=self.hardware, host=self.host, source_path=self.source_path,
                    source_sha256=self.source_sha256, size_bytes=self.size_bytes,
                    parent_key=f"{self.trace_key}#{forward.forward_id}",
                    start_ns=forward.head_start_ns, end_ns=forward.head_end_ns,
                    value_ms=head_ms, count=None, op_type=None, core=None,
                    forward_id=forward.forward_id, layer_id=None, reason=None,
                    detail={"boundary": "raw vocabulary-head interval"})
        for layer in self.layer_windows:
            yield NativeTarget(
                key=f"{self.trace_key}#{layer.forward_id}#L{layer.layer_id}",
                kind="layer", status="measured", cell_id=self.cell_id,
                phase=self.phase, trace_key=self.trace_key, rank=self.rank,
                device_id=self.device_id, hardware=self.hardware, host=self.host,
                source_path=self.source_path, source_sha256=self.source_sha256,
                size_bytes=self.size_bytes,
                parent_key=f"{self.trace_key}#{layer.forward_id}",
                start_ns=layer.start_ns, end_ns=layer.end_ns, value_ms=layer.span_ms,
                count=None, op_type=None, core=None, forward_id=layer.forward_id,
                layer_id=layer.layer_id, reason=None,
                detail={"activity_ms": layer.activity_ms,
                        "internal_gap_ms": layer.internal_gap_ms,
                        "attention": layer.attention, "kind": layer.kind,
                        "identity_status": layer.identity_status})
        for aggregate in self.layer_aggregates:
            yield NativeTarget(
                key=f"{self.trace_key}#L{aggregate.layer_id}",
                kind="layer_aggregate", status="measured", cell_id=self.cell_id,
                phase=self.phase, trace_key=self.trace_key, rank=self.rank,
                device_id=self.device_id, hardware=self.hardware, host=self.host,
                source_path=self.source_path, source_sha256=self.source_sha256,
                size_bytes=self.size_bytes, parent_key=self.trace_key,
                start_ns=None, end_ns=None, value_ms=aggregate.mean_ms,
                count=aggregate.count, op_type=None, core=None, forward_id=None,
                layer_id=aggregate.layer_id, reason=None,
                detail={"p50_ms": aggregate.p50_ms, "min_ms": aggregate.min_ms,
                        "max_ms": aggregate.max_ms,
                        "activity_mean_ms": aggregate.activity_mean_ms,
                        "gap_mean_ms": aggregate.gap_mean_ms,
                        "per_stream_additive_ms": aggregate.per_stream,
                        "identity_status": "inferred_from_complete_declared_topology"})


@dataclass(frozen=True)
class NativeTarget:
    key: str
    kind: str
    status: str
    cell_id: str
    phase: str
    trace_key: str
    rank: int | None
    device_id: int | None
    hardware: Mapping[str, Any]
    host: str
    source_path: str
    source_sha256: str
    size_bytes: int
    parent_key: str | None
    start_ns: int | None
    end_ns: int | None
    value_ms: float | None
    count: int | None
    op_type: str | None
    core: str | None
    forward_id: str | None
    layer_id: int | None
    reason: str | None
    detail: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION, "key": self.key, "kind": self.kind,
            "status": self.status, "cell_id": self.cell_id, "phase": self.phase,
            "trace_key": self.trace_key, "rank": self.rank,
            "device_id": self.device_id,
            "hardware": dict(self.hardware) if self.hardware else None,
            "host": self.host, "source_path": self.source_path,
            "source_sha256": self.source_sha256, "size_bytes": self.size_bytes,
            "parent_key": self.parent_key, "start_ns": self.start_ns,
            "end_ns": self.end_ns, "value_ms": self.value_ms, "count": self.count,
            "op_type": self.op_type, "core": self.core,
            "forward_id": self.forward_id, "layer_id": self.layer_id,
            "reason": self.reason, "detail": _plain(self.detail),
        }


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Timetable construction
# ---------------------------------------------------------------------------

def _read_opstat(path: Path) -> tuple[str | None, tuple[str, ...], str]:
    if not path.is_file():
        return None, (), "op_statistic_missing"
    digest, _size = _sha256(path)
    devices: set[str] = set()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                device = str(row.get("Device_id") or "").strip()
                if device:
                    devices.add(device)
    except (OSError, csv.Error):
        return digest, (), "op_statistic_unreadable"
    return digest, tuple(sorted(devices)), "present"


def _forward_from_decode(result: Mapping[str, Any]) -> ForwardMeasurement:
    geometry = result.get("geometry") or {}
    layers = [stage for stage in result.get("stages") or ()
              if stage.get("layer_id") is not None]
    return ForwardMeasurement(
        forward_id=str(result.get("forward_id")),
        status=str(result.get("status") or "unresolved"),
        start_ns=result.get("start_ns"), end_ns=result.get("end_ns"),
        span_ms=result.get("body_forward_span_ms"),
        activity_ms=result.get("body_activity_ms"),
        internal_gap_ms=result.get("body_internal_gap_ms"),
        head_start_ns=result.get("head_start_ns"),
        head_end_ns=result.get("head_end_ns"),
        query_rows=result.get("query_rows"),
        sequences_per_replica=geometry.get("sequences_per_replica"),
        tokens_per_sequence=geometry.get("tokens_per_sequence"),
        layer_count=(result.get("confidence") or {}).get("matched_layers"),
        basis=str(result.get("basis") or ""))


def _layers_from_decode(result: Mapping[str, Any]) -> list[LayerMeasurement]:
    rows = []
    for stage in result.get("stages") or ():
        if stage.get("layer_id") is None:
            continue
        rows.append(LayerMeasurement(
            forward_id=str(result.get("forward_id")), layer_id=int(stage["layer_id"]),
            start_ns=stage.get("start_ns"), end_ns=stage.get("end_ns"),
            span_ms=float(stage["span_ms"]),
            activity_ms=stage.get("device_activity_union_ms"),
            internal_gap_ms=stage.get("internal_uncovered_gap_ms"),
            attention=(stage.get("plan") or {}).get("attention"),
            kind=str(stage.get("kind") or ""),
            identity_status="inferred_from_complete_declared_topology"))
    return rows


def _aggregates_from_decode(report: Mapping[str, Any]) -> tuple[LayerAggregate, ...]:
    rows = []
    for group in report.get("per_layer_ms") or ():
        stats = group.get("stats") or {}
        rows.append(LayerAggregate(
            layer_id=int(group["layer_id"]), count=int(group.get("total_count") or 0),
            mean_ms=stats.get("mean"), p50_ms=stats.get("p50"),
            min_ms=stats.get("min"), max_ms=stats.get("max"),
            activity_mean_ms=(group.get("activity_ms_stats") or {}).get("mean"),
            gap_mean_ms=(group.get("internal_gap_ms_stats") or {}).get("mean"),
            per_stream=tuple((item["stream_id"], (item.get("stats") or {}).get("mean") or 0.0)
                             for item in group.get("per_stream_activity_ms") or ())))
    return tuple(sorted(rows, key=lambda item: item.layer_id))


def _forward_from_prefill(result: Mapping[str, Any]) -> ForwardMeasurement:
    body = result.get("body") or {}
    head = result.get("head") or {}
    return ForwardMeasurement(
        forward_id=str(result.get("forward_id")), status="measured",
        start_ns=body.get("start_ns"), end_ns=body.get("end_ns"),
        span_ms=body.get("span_ms"), activity_ms=body.get("device_activity_union_ms"),
        internal_gap_ms=body.get("internal_uncovered_gap_ms"),
        head_start_ns=head.get("start_ns"), head_end_ns=head.get("end_ns"),
        query_rows=result.get("query_rows"), sequences_per_replica=None,
        tokens_per_sequence=None, layer_count=result.get("matched_layer_count"),
        basis=str(result.get("basis") or ""))


def _layers_from_prefill(result: Mapping[str, Any]) -> list[LayerMeasurement]:
    return [LayerMeasurement(
        forward_id=str(result.get("forward_id")), layer_id=int(layer["layer_id"]),
        start_ns=layer.get("start_ns"), end_ns=layer.get("end_ns"),
        span_ms=float(layer["span_ms"]),
        activity_ms=layer.get("device_activity_union_ms"),
        internal_gap_ms=layer.get("internal_uncovered_gap_ms"),
        attention=layer.get("attention"), kind="prefill_layer",
        identity_status="inferred_from_complete_declared_topology")
        for layer in result.get("layers") or ()]


def _aggregates_from_prefill(forwards: Sequence[Mapping[str, Any]]) -> tuple[LayerAggregate, ...]:
    groups: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for forward in forwards:
        for layer in forward.get("layers") or ():
            groups[int(layer["layer_id"])].append(layer)
    rows = []
    for layer_id, values in sorted(groups.items()):
        spans = [float(value["span_ms"]) for value in values]
        activity = [float(value.get("device_activity_union_ms") or 0.0) for value in values]
        gaps = [float(value.get("internal_uncovered_gap_ms") or 0.0) for value in values]
        ordered = sorted(spans)
        rows.append(LayerAggregate(
            layer_id=layer_id, count=len(spans), mean_ms=sum(spans) / len(spans),
            p50_ms=ordered[len(ordered) // 2], min_ms=ordered[0], max_ms=ordered[-1],
            activity_mean_ms=sum(activity) / len(activity),
            gap_mean_ms=sum(gaps) / len(gaps), per_stream=()))
    return tuple(rows)


def _timetable(row: Mapping[str, Any], source: CellSource, path: Path, *,
               max_rows: int, timeout_s: float,
               roots: tuple[str, ...],
               declaration: Mapping[str, Any] | str | Path | None = None,
               terminal_receipts: Mapping[str, list[dict[str, Any]]] | None = None
               ) -> TraceTimetable:
    cell_id = str(row.get("cell_id") or "")
    phase = str(row.get("phase") or "")
    host = path.parent.parent.name
    worker = path.parent.name
    launch = _launch_for(source.case_dir, host)
    hardware = _hardware_for(source.case_dir, host)
    sha, size = _sha256(path)
    stream_sha = _decompressed_sha(path)
    source_class, source_evidence = _source_classification(
        source, path, size, stream_sha, host, worker, roots, terminal_receipts)
    source_evidence = {**source_evidence, "compressed_sha256": sha}
    opstat_sha, opstat_devices, opstat_status = _read_opstat(path.parent / "op_statistic.csv")
    device_id = _int(opstat_devices[0]) if len(opstat_devices) == 1 else None
    if len(opstat_devices) > 1:
        device_id = None
    rank, rank_basis, rank_conflict = _worker_rank(launch, device_id, worker)
    trace_key = f"{cell_id}::{phase}::{host}::{worker}::{sha[:16]}"
    launch_detail = {
        "dp_start": launch.dp_start if launch else None,
        "dp_local": launch.dp_local if launch else None,
        "dp": launch.dp if launch else None,
        "tp": launch.tp if launch else None,
        "pp": launch.pp if launch else None,
        "source": launch.source if launch else None,
    }
    hardware_basis = str(hardware.get("basis") or "preflight_unavailable")
    hardware_key = hardware.get("hardware_key")

    limitations = ["per-rank true observations; no global client critical-path selection"]
    scan: _Scan
    schema: Any
    forwards: list[ForwardMeasurement] = []
    layer_windows: list[LayerMeasurement] = []
    aggregates: tuple[LayerAggregate, ...] = ()
    scan_counts: dict[str, Any] = {}
    reason: str | None = None
    declaration_detail: Mapping[str, Any] = {}

    if phase not in _PHASES:
        scan, schema, scan_error = _safe_scan(
            path, rank_id="" if rank is None else str(rank),
            max_rows=max_rows, timeout_s=timeout_s)
        status = "raw_only"
        reason = (f"source_scan_error:{scan_error}" if scan_error else
                  f"phase_not_supported:{phase or 'absent'}")
    elif phase == "decode":
        raw, config, model_error, declaration_detail = _model_config(
            row, source.case_dir, host, declaration)
        if config is None:
            scan, schema, scan_error = _safe_scan(
                path, rank_id="" if rank is None else str(rank),
                max_rows=max_rows, timeout_s=timeout_s)
            status = "raw_only"
            reason = (f"source_scan_error:{scan_error}" if scan_error else model_error)
        else:
            ref = SourceRef(
                rank_id="" if rank is None else str(rank), rank_index=rank,
                kind="kernel_details_csv", path=str(path.resolve()),
                basename=path.name, sha256=sha, size_bytes=size,
                schema_version="kernel_details_csv", schema_variant="resolved_by_probe",
                header_sha256=None, optional_missing=(), notes=(),
                mtime_ns=path.stat().st_mtime_ns)
            try:
                scan, schema, report = _decode_timetable(
                    path, config, ref, rank_id=ref.rank_id,
                    max_rows=max_rows, timeout_s=timeout_s)
            except (ProfilerUsageError, ProfilerSchemaError, ProfilerQueryError,
                    ValueError, KeyError) as exc:
                scan, schema, scan_error = _safe_scan(
                    path, rank_id=ref.rank_id, max_rows=max_rows,
                    timeout_s=timeout_s)
                status = "raw_only"
                reason = (f"source_scan_error:{scan_error}" if scan_error else
                          f"decode_segmentation_limit:{type(exc).__name__}:{exc}")
            else:
                forwards = [_forward_from_decode(item) for item in report.get("forwards") or ()]
                for item in report.get("forwards") or ():
                    layer_windows.extend(_layers_from_decode(item))
                aggregates = _aggregates_from_decode(report)
                scan_counts = dict(report.get("scan_counts") or {})
                if forwards:
                    status = "measured"
                else:
                    status = "raw_only"
                    anomalies = report.get("anomaly_counts") or {}
                    reason = "decode_segmentation_unresolved:" + ",".join(
                        f"{key}={value}" for key, value in sorted(anomalies.items()))
    else:
        raw, _config, model_error, declaration_detail = _model_config(
            row, source.case_dir, host, declaration)
        scan, schema, scan_error = _safe_scan(
            path, rank_id="" if rank is None else str(rank),
            max_rows=max_rows, timeout_s=timeout_s)
        if scan_error:
            status = "raw_only"
            reason = f"source_scan_error:{scan_error}"
        elif raw is None:
            status = "raw_only"
            reason = model_error
        else:
            try:
                observed, evidence = _prefill_observation(
                    raw, path, max_rows=max_rows, timeout_s=timeout_s)
            except (OSError, ValueError, KeyError, ProfilerSchemaError,
                    ProfilerQueryError) as exc:
                observed, evidence = None, {
                    "reason": f"prefill_extraction_error:{type(exc).__name__}:{exc}"}
            if observed is None or not observed.get("forwards"):
                status = "raw_only"
                reason = "prefill_extraction_unresolved:" + str(
                    evidence.get("reason") if isinstance(evidence, Mapping) else evidence)
            else:
                declared = (observed.get("source_identity") or {}).get("sha256")
                if declared and declared != sha:
                    status = "raw_only"
                    reason = "source_changed_during_extraction"
                else:
                    for item in observed["forwards"]:
                        forwards.append(_forward_from_prefill(item))
                        layer_windows.extend(_layers_from_prefill(item))
                    aggregates = _aggregates_from_prefill(observed["forwards"])
                    scan_counts = dict(observed.get("scan_counts") or {})
                    status = "measured"

    scan_counts = {
        **scan_counts, "raw_rows": scan.rows, "raw_positive_events": scan.positive,
        "raw_invalid_timing_rows": scan.bad_rows,
        "raw_additive_ns": scan.additive_ns,
    }
    header_sha = getattr(schema, "header_sha256", None)
    schema_version = getattr(schema, "schema_version", "unknown")
    schema_variant = getattr(schema, "schema_variant", "unknown")
    optional_missing = tuple(getattr(schema, "optional_missing", ()))
    operators = scan.operator_cells()
    streams = scan.stream_spans()
    device_consistent = True
    if scan.device_ids and len(scan.device_ids) > 1:
        status = "raw_only" if status == "measured" else status
        reason = (reason + ";" if reason else "") + "multiple_raw_device_ids"
        device_consistent = False
    if device_id is not None and scan.device_ids and str(device_id) not in scan.device_ids:
        status = "raw_only" if status == "measured" else status
        reason = (reason + ";" if reason else "") + "device_id_mismatch_between_opstat_and_kernel"
        device_consistent = False
    boundaries = {
        "raw_span": scan.span_ms is not None,
        "operators": bool(operators),
        "streams": bool(streams),
        "forwards": bool(forwards),
        "heads": any(item.head_start_ns is not None and item.head_end_ns is not None
                     for item in forwards),
        "layers": bool(layer_windows),
        "layer_aggregates": bool(aggregates),
        "rank": rank is not None,
        "device_consistent": device_consistent,
        "hardware": bool(hardware_key),
    }
    return TraceTimetable(
        cell_id=cell_id, phase=phase, trace_key=trace_key,
        source_path=str(path.resolve()), source_sha256=sha,
        raw_stream_sha256=stream_sha, size_bytes=size,
        source_class=source_class, source_evidence=source_evidence,
        model_binding=declaration_detail,
        header_sha256=header_sha, schema_version=schema_version,
        schema_variant=schema_variant, optional_missing=optional_missing,
        host=host, worker=worker, rank=rank, device_id=device_id,
        rank_basis=rank_basis, rank_conflict=rank_conflict,
        hardware=hardware, hardware_basis=hardware_basis,
        launch=launch_detail, status=status, reason=reason,
        raw_start_ns=scan.first_start_ns, raw_end_ns=scan.last_end_ns,
        raw_span_ms=scan.span_ms, raw_additive_ms=scan.additive_ms,
        streams=streams, operators=operators, opstat_sha256=opstat_sha,
        opstat_device_ids=opstat_devices, opstat_status=opstat_status,
        forwards=tuple(forwards), layer_windows=tuple(layer_windows),
        layer_aggregates=aggregates, scan_counts=scan_counts,
        boundaries=boundaries, declaration=declaration_detail,
        limitations=tuple(limitations))


# ---------------------------------------------------------------------------
# Public streaming API
# ---------------------------------------------------------------------------

def iter_trace_timetables(row: Mapping[str, Any], *, roots: Sequence[Path | str] | None = None,
                          phases: Sequence[str] | None = None,
                          declaration: Mapping[str, Any] | str | Path | None = None,
                          receipts: Any = None,
                          max_rows: int = MAX_ROWS,
                          timeout_s: float = TIMEOUT_S) -> Iterator[TraceTimetable]:
    """Yield every retained raw timetable for one original enrolled row.

    One timetable is materialised at a time.  Multiple captures of the same
    enrolled ID stay separate and each is individually keyed.  A missing cell
    still yields one explicit ``missing_source`` timetable so the caller can
    keep the row in inventory.
    """
    cell_id = str(row.get("cell_id") or "")
    phase = str(row.get("phase") or "")
    if not cell_id:
        raise ValueError("enrolled_row_requires_cell_id")
    wanted = tuple(phases) if phases else (phase,)
    resolved_roots = _resolve_roots(roots)
    root_names = tuple(str(path.resolve()) for path in resolved_roots)
    terminal_receipts = _terminal_receipt_index(receipts)
    sources = _index(root_names).get(cell_id, ())
    if phase and phase not in wanted:
        return
    if not sources:
        yield TraceTimetable(
            cell_id=cell_id, phase=phase, trace_key=f"{cell_id}::{phase}::missing_source",
            source_path="", source_sha256="", raw_stream_sha256=None, size_bytes=0,
            source_class="missing_source", source_evidence={}, model_binding={},
            header_sha256=None,
            schema_version="unknown", schema_variant="unknown", optional_missing=(),
            host="", worker="", rank=None, device_id=None,
            rank_basis="source_not_retained", rank_conflict=None, hardware={},
            hardware_basis="preflight_unavailable",
            launch={}, status="missing_source", reason="cell_directory_not_retained",
            raw_start_ns=None, raw_end_ns=None,
            raw_span_ms=None, raw_additive_ms=0.0, streams=(), operators=(),
            opstat_sha256=None, opstat_device_ids=(), opstat_status="op_statistic_missing",
            forwards=(), layer_windows=(), layer_aggregates=(), scan_counts={},
            boundaries={"raw_span": False, "operators": False, "streams": False,
                        "forwards": False, "heads": False, "layers": False,
                        "layer_aggregates": False, "rank": False,
                        "device_consistent": False, "hardware": False},
            declaration={}, limitations=("row retained in inventory; no retained raw source",))
        return
    for cell_source in sources:
        for path in cell_source.traces:
            yield _timetable(row, cell_source, path, max_rows=max_rows,
                             timeout_s=timeout_s, declaration=declaration,
                             roots=root_names, terminal_receipts=terminal_receipts)


def iter_native_targets(row: Mapping[str, Any], *, roots: Sequence[Path | str] | None = None,
                        phases: Sequence[str] | None = None,
                        include: Sequence[str] | None = None,
                        declaration: Mapping[str, Any] | str | Path | None = None,
                        receipts: Any = None,
                        max_rows: int = MAX_ROWS,
                        timeout_s: float = TIMEOUT_S) -> Iterator[NativeTarget]:
    """Stream independently keyed targets for one original enrolled row.

    ``include`` may narrow the emitted kinds (``trace``, ``operator``,
    ``forward``, ``head``, ``layer``, ``layer_aggregate``).  Every target
    carries its own key, source SHA, rank/device and status so consumers do not
    share mutable global state.
    """
    allowed = set(include) if include else None
    for timetable in iter_trace_timetables(
            row, roots=roots, phases=phases, declaration=declaration,
            receipts=receipts, max_rows=max_rows, timeout_s=timeout_s):
        for target in timetable.targets():
            if allowed is None or target.kind in allowed:
                yield target


def iter_enrolled_rows(path: Path | str) -> Iterator[dict[str, Any]]:
    """Stream the original enrolled JSONL without copying the full population."""
    source = Path(path)
    opener = gzip.open if source.name.endswith(".gz") else open
    with opener(source, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def summarize_targets(targets: Iterable[NativeTarget]) -> dict[str, Any]:
    """Count kinds/statuses without retaining targets (caller keeps keys)."""
    counts: Counter[str] = Counter()
    status: Counter[str] = Counter()
    source_classes: Counter[str] = Counter()
    source_grades: Counter[str] = Counter()
    traces = set()
    independent: set[str] = set()
    current_positive = exact_identity = 0
    stale = shared = 0
    forward_values: list[float] = []
    for target in targets:
        counts[target.kind] += 1
        status[f"{target.kind}:{target.status}"] += 1
        if target.kind == "trace":
            traces.add(target.trace_key)
            detail = target.detail or {}
            source_class = str(detail.get("source_class") or "unknown")
            source_classes[source_class] += 1
            evidence = detail.get("source_evidence") or {}
            grade = evidence.get("source_grade")
            if grade:
                source_grades[str(grade)] += 1
            if evidence.get("exact_identity") is True:
                exact_identity += 1
            if source_class in {"actual", "shared_payload"}:
                current_positive += 1
                key = str(evidence.get("independent_source_key") or target.trace_key)
                independent.add(key)
            if source_class == "stale_superseded":
                stale += 1
            if source_class == "shared_payload":
                shared += 1
        elif target.kind == "forward" and target.value_ms is not None:
            forward_values.append(target.value_ms)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_counts": dict(sorted(counts.items())),
        "status_counts": dict(sorted(status.items())),
        "trace_count": len(traces),
        "source_class_counts": dict(sorted(source_classes.items())),
        "source_grade_counts": dict(sorted(source_grades.items())),
        "current_positive_trace_count": current_positive,
        "exact_identity_trace_count": exact_identity,
        "independent_source_count": len(independent),
        "stale_trace_count": stale,
        "shared_trace_count": shared,
        "forward_count": len(forward_values),
        "forward_span_ms": _stats(forward_values),
    }


def _stats(values: Sequence[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    return {"count": len(ordered), "mean": sum(ordered) / len(ordered),
            "min": ordered[0], "max": ordered[-1],
            "p50": ordered[len(ordered) // 2]}
