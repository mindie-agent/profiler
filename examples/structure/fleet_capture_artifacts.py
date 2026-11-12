"""Raw artifact parsers, source identity, and typed measurement scopes.

[Role]
  Artifact I/O for `fleet_capture_observations`: streaming CSV/JSON parsers,
  exact op scopes, client/harness receipts, bounded timelines, and direct
  same-capture source resolution.  No simulator/prediction dependency.

[Invariants] Raw mass is never divided by a declared forward count; header-only
artifacts are missing evidence; absent core is UNKNOWN; no sibling rank/cell or
arbitrary row path is borrowed.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "fleet-capture-observations/2"
DEFAULT_DATA_ROOTS = (Path("/Volumes/data/mindie-sim-data"),
                      Path("/Users/maoxx241/code/mindie-agent/.workstreams"),
                      Path("/Users/maoxx241/code"))
DATA_ROOTS: tuple[Path, ...] = DEFAULT_DATA_ROOTS
MULTINODE_RUNS_ROOT = Path("/Volumes/data/mindie-sim-data/a5/multinode-full-coverage-20261108/runs")
RESULTS_DIR = Path(__file__).resolve().parent / "results"
CASES_PATH = Path(__file__).resolve().parent / "cases.json"

_CLIENT_FILE = "request_summary.csv"
_STEP_MARKERS = ("_compute_slot_mapping_kernel", "_compute_slot_mappings_kernel")
_CACHE_LIMIT = 384
_FILE_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}
_CLIENT_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}
_SHA_CACHE: dict[tuple[str, int, int], str | None] = {}
_RESULTS_SOURCE_INDEX: dict[str, dict[str, Any]] = {}
_MULTINODE_INDEX: dict[str, Path] | None = None
_FORWARD_WINDOW_PATH: Path | None = None
_FORWARD_WINDOW_INDEX: dict[str, dict[str, Any]] | None = None
_REGISTERED_EXTRACTION_INDEX: dict[tuple[str, str], Path] | None = None
_RECEIPT_INDEX_PATH: Path | None = None
_RECEIPT_INDEX: dict[str, dict[str, Any]] | None = None
_REGISTERED_FORWARD_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}
# Exact historical-path -> recovered same-bytes source.  Used only when the
# recorded path is absent and both size and streamed SHA-256 match.
_RECOVERED_SOURCES: dict[str, dict[str, Any]] = {
    "/Volumes/data-tmp/tmp/mindie-body-profiling-kimi-op-summary.csv": {
        "path": "/Volumes/data/mindie-sim-data/a5/kimi_k3_w4a8_mxfp_dp4_tp8_ep32_p32k_20261030/raw/prof-export/op_summary_20261023053244.csv",
        "size_bytes": 110031770,
        "sha256": "ab1d44d3613ecb92d71af6d790ab9dfc72be5aabfe92bf4f99d584fbd0f9e648",
    },
}

def _recovered_source(path: Path | str) -> Path | None:
    record = _RECOVERED_SOURCES.get(str(path))
    if not record:
        return None
    candidate = Path(str(record["path"]))
    try:
        if candidate.stat().st_size != int(record["size_bytes"]):
            return None
    except OSError:
        return None
    if _sha256_file(candidate) != str(record["sha256"]).lower():
        return None
    return candidate

def configure_observation_roots(*, data_roots: Sequence[Path] | None = None,
                                multinode_root: Path | None = None,
                                results_dir: Path | None = None,
                                forward_windows: Path | None = None,
                                cases_path: Path | None = None,
                                receipt_index: Path | None = None) -> None:
    """Point the module at alternate roots (A/C test wiring)."""
    global DATA_ROOTS, MULTINODE_RUNS_ROOT, RESULTS_DIR, _FORWARD_WINDOW_PATH, CASES_PATH, _RECEIPT_INDEX_PATH
    if data_roots is not None:
        DATA_ROOTS = tuple(Path(p) for p in data_roots)
    if multinode_root is not None:
        MULTINODE_RUNS_ROOT = Path(multinode_root)
    if results_dir is not None:
        RESULTS_DIR = Path(results_dir)
    if forward_windows is not None:
        _FORWARD_WINDOW_PATH = Path(forward_windows)
    if cases_path is not None:
        CASES_PATH = Path(cases_path)
    if receipt_index is not None:
        _RECEIPT_INDEX_PATH = Path(receipt_index)
    from fleet_source_discovery import configure_discovery_roots
    configure_discovery_roots(data_roots=DATA_ROOTS)
    clear_observation_caches()

def clear_observation_caches() -> None:
    _FILE_CACHE.clear(); _CLIENT_CACHE.clear(); _SHA_CACHE.clear(); _RESULTS_SOURCE_INDEX.clear()
    global _MULTINODE_INDEX, _FORWARD_WINDOW_INDEX, _REGISTERED_EXTRACTION_INDEX, _RECEIPT_INDEX
    _MULTINODE_INDEX = None
    _FORWARD_WINDOW_INDEX = None
    _REGISTERED_EXTRACTION_INDEX = None
    _RECEIPT_INDEX = None
    _REGISTERED_FORWARD_CACHE.clear()

clear_caches = clear_observation_caches

def _stat_key(path: Path) -> tuple[str, int, int] | None:
    try:
        st = path.stat()
    except OSError:
        return None
    return (str(path), st.st_mtime_ns, st.st_size)

def _cache_put(cache: dict[Any, Any], key: Any, value: Any) -> None:
    if len(cache) >= _CACHE_LIMIT:
        cache.clear()
    cache[key] = value

def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="")
    return path.open("rt", encoding="utf-8", errors="replace", newline="")


def _as_float(raw: Any, label: str, path: Path) -> float:
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"malformed {label} in {path}: {raw!r}") from exc
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"malformed {label} in {path}: {raw!r}")
    return value
def _clean_rel(text: str) -> str:
    cleaned = re.sub(r"(?i)ascend(?:910b|950(?:pr|dt)?)[_-]?", "", str(text or ""))
    return re.sub(r"\b(?:177\.(?:25|31)|192\.168|173\.125)\.\d{1,3}\.\d{1,3}\b", "node", cleaned)


def _base_capture_id(cid: str) -> str:
    return re.sub(r"#\d+$", "", str(cid or ""))


def _sha256_file(path: Path, max_bytes: int = 1024 * 1024 * 1024) -> str | None:
    try:
        st = path.stat()
    except OSError:
        return None
    key = (str(path), st.st_mtime_ns, st.st_size, st.st_ino)
    if key is None:
        return None
    if key in _SHA_CACHE:
        return _SHA_CACHE[key]
    digest, total = hashlib.sha256(), 0
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    _SHA_CACHE[key] = None
                    return None
                digest.update(chunk)
    except OSError:
        return None
    value = digest.hexdigest()
    _SHA_CACHE[key] = value
    return value
def _normalise_ops(ops: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for op_type, entry in ops.items():
        if isinstance(entry, Mapping):
            out[str(op_type)] = {"core": str(entry.get("core") or "UNKNOWN"),
                                 "count": int(entry.get("count") or 0),
                                 "total_us": round(float(entry.get("total_us") or entry.get("duration_us") or 0.0), 6)}
        else:
            out[str(op_type)] = {"core": "UNKNOWN", "count": 0, "total_us": round(float(entry or 0.0), 6)}
    return out

def parse_kernel_details_summary(kd_path: Path | str) -> dict[str, Any]:
    """Stream kernel/op_summary CSV into exact row/core/op totals (no core guess)."""
    path = Path(kd_path)
    key = _stat_key(path)
    if key is not None and key in _FILE_CACHE:
        return _FILE_CACHE[key]
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))
    rows, total = 0, 0.0
    by_core: dict[str, float] = {}
    core_counts: Counter[str] = Counter()
    ops: dict[str, dict[str, Any]] = {}
    by_op_engine: dict[str, dict[str, Any]] = {}
    first_start, last_end = None, None
    with _open_text(path) as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"empty kernel_details header in {path}")
        for row in reader:
            raw_dur = row.get("Duration(us)")
            if raw_dur is None:
                raw_dur = row.get("Task Duration(us)")
            if raw_dur is None:
                raw_dur = row.get("Duration(ns)")
                divisor = 1000.0
            else:
                divisor = 1.0
            if raw_dur is None or str(raw_dur).strip() == "":
                raise ValueError(f"malformed duration cell in {path}: {raw_dur!r}")
            dur = _as_float(raw_dur, "duration cell", path) / divisor
            name = str(row.get("Type") or row.get("OP Type") or row.get("Name") or "Kernel").strip()
            core = str(row.get("Accelerator Core") or row.get("Core Type") or row.get("Task Type") or "").strip()
            if not core or core == "N/A":
                core = "UNKNOWN"
            rows += 1
            total += dur
            by_core[core] = by_core.get(core, 0.0) + dur
            core_counts[core] += 1
            cur = ops.setdefault(name, {"core": core, "count": 0, "total_us": 0.0, "min_us": dur, "max_us": dur})
            cur["count"] += 1
            cur["total_us"] += dur
            cur["min_us"] = min(cur["min_us"], dur)
            cur["max_us"] = max(cur["max_us"], dur)
            if cur["core"] != core and cur["core"] != "MIXED":
                cur["core"] = "MIXED"
            eng = by_op_engine.setdefault(f"{name}\x1f{core}",
                                          {"op_type": name, "core": core, "count": 0, "total_us": 0.0})
            eng["count"] += 1
            eng["total_us"] += dur
            raw_start = row.get("Start Time(us)") or row.get("Task Start Time(us)")
            if raw_start not in (None, "", "N/A"):
                try:
                    begin = float(str(raw_start).strip())
                except (TypeError, ValueError):
                    begin = None
                if begin is not None and math.isfinite(begin):
                    first_start = begin if first_start is None else min(first_start, begin)
                    end = begin + dur
                    last_end = end if last_end is None else max(last_end, end)
    result = {
        "source_kind": "kernel_details", "source_path": str(path),
        "total_kernel_rows": rows, "total_kernel_duration_us": round(total, 6),
        "by_accelerator_core": {k: round(v, 6) for k, v in sorted(by_core.items())},
        "by_accelerator_core_counts": dict(sorted(core_counts.items())),
        "ops": {k: {**v, "total_us": round(v["total_us"], 6), "min_us": round(v["min_us"], 6), "max_us": round(v["max_us"], 6)}
                for k, v in ops.items()},
        "by_op_engine": {k: {**v, "total_us": round(v["total_us"], 6)} for k, v in by_op_engine.items()},
        "top_op_types": [{"type": k, "core": v["core"], "count": v["count"], "total_us": round(v["total_us"], 2)}
                         for k, v in sorted(ops.items(), key=lambda item: -item[1]["total_us"])[:5]],
        "first_start_us": first_start, "last_end_us": last_end,
        "span_us": (last_end - first_start) if (first_start is not None and last_end is not None) else None,
    }
    if key is not None:
        _cache_put(_FILE_CACHE, key, result)
    return result


def parse_op_statistic_summary(path: Path | str) -> dict[str, Any]:
    """Parse `op_statistic.csv`; strict count/duration cells, raw core names."""
    op_path = Path(path)
    if op_path.is_dir():
        op_path = op_path / "op_statistic.csv"
    key = _stat_key(op_path)
    if key is not None and key in _FILE_CACHE:
        return _FILE_CACHE[key]
    if not op_path.exists() or not op_path.is_file():
        raise FileNotFoundError(str(op_path))
    rows, total = 0, 0.0
    by_core: dict[str, float] = {}
    core_counts: Counter[str] = Counter()
    ops: dict[str, dict[str, Any]] = {}
    by_op_engine: dict[str, dict[str, Any]] = {}
    with op_path.open("rt", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            raw_cnt, raw_dur = row.get("Count"), row.get("Total Time(us)")
            if raw_cnt is None or str(raw_cnt).strip() == "" or raw_dur is None or str(raw_dur).strip() == "":
                raise ValueError(f"malformed numeric cell in {op_path}: Count={raw_cnt!r} Total Time(us)={raw_dur!r}")
            dur = _as_float(raw_dur, "Total Time(us)", op_path)
            count_f = _as_float(raw_cnt, "Count", op_path)
            if not count_f.is_integer() or "." in str(raw_cnt).strip():
                raise ValueError(f"fractional Count is not an integer in {op_path}: Count={raw_cnt!r}")
            count = int(count_f)
            core = str(row.get("Core Type") or "UNKNOWN").strip() or "UNKNOWN"
            op_type = str(row.get("OP Type") or "UNKNOWN").strip() or "UNKNOWN"
            rows += count
            total += dur
            by_core[core] = by_core.get(core, 0.0) + dur
            core_counts[core] += count
            cur = ops.setdefault(op_type, {"core": core, "count": 0, "total_us": 0.0})
            cur["count"] += count
            cur["total_us"] += dur
            if cur["core"] != core and cur["core"] != "MIXED":
                cur["core"] = "MIXED"
            eng = by_op_engine.setdefault(f"{op_type}\x1f{core}",
                                          {"op_type": op_type, "core": core, "count": 0, "total_us": 0.0})
            eng["count"] += count
            eng["total_us"] += dur
    if total <= 0.0:
        return {}
    result = {
        "source_kind": "op_statistic", "source_path": str(op_path),
        "total_kernel_rows": rows, "total_kernel_duration_us": round(total, 6),
        "by_accelerator_core": {k: round(v, 6) for k, v in sorted(by_core.items())},
        "by_accelerator_core_counts": dict(sorted(core_counts.items())),
        "ops": {k: {**v, "total_us": round(v["total_us"], 6)} for k, v in ops.items()},
        "by_op_engine": {k: {**v, "total_us": round(v["total_us"], 6)} for k, v in by_op_engine.items()},
        "top_op_types": [{"type": k, "core": v["core"], "count": v["count"], "total_us": round(v["total_us"], 2)}
                         for k, v in sorted(ops.items(), key=lambda item: -item[1]["total_us"])[:5]],
        "first_start_us": None, "last_end_us": None, "span_us": None,
    }
    if key is not None:
        _cache_put(_FILE_CACHE, key, result)
    return result


def _parse_float_cell(raw: Any) -> float | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _median(values: Iterable[float | None]) -> float | None:
    vals = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else 0.5 * (vals[mid - 1] + vals[mid])


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _client_from_measurement_json(path: Path) -> dict[str, Any] | None:
    """Native harness record: harness aggregates + per-stream receipts."""
    data = _read_json(path)
    if not data:
        return None
    streams = [s for s in (data.get("streams") or ()) if isinstance(s, Mapping)]
    ok_streams = [s for s in streams if s.get("ok") is not False]
    completion = [s.get("completion_tokens") for s in ok_streams if s.get("completion_tokens") is not None]
    ttft_s = data.get("ttft_mean_s", data.get("ttft_ms_mean", data.get("ttft_p50_s")))
    tpot_s = data.get("tpot_mean_s", data.get("tpot_ms_mean", data.get("tpot_p50_s")))
    if ttft_s is None:
        ttft_s = next((s.get("ttft_s") for s in ok_streams if s.get("ttft_s") is not None), None)
    if tpot_s is None:
        tpot_s = next((s.get("itl_mean_s") for s in ok_streams if s.get("itl_mean_s") is not None), None)
    if ttft_s is None and tpot_s is None:
        return None
    def _ms(value: Any) -> float | None:
        return float(value) * 1000.0 if value is not None else None
    tpot_ms = float(data["tpot_ms_mean"]) if data.get("tpot_ms_mean") is not None else _ms(tpot_s)
    ttft_ms = float(data["ttft_ms_mean"]) if data.get("ttft_ms_mean") is not None else _ms(ttft_s)
    n_requests = int(data.get("success") if data.get("success") is not None else
                     (data.get("n_requests") or len(ok_streams) or 0))
    if completion:
        completion_tokens = int(sum(float(v) for v in completion))
        evidence = "client_decode_tokens" if completion_tokens > (len(ok_streams) or n_requests) else "no_decode_tokens"
    elif data.get("completion_tokens") is not None:
        completion_tokens = int(float(data["completion_tokens"]))
        evidence = "client_decode_tokens" if completion_tokens > n_requests else "no_decode_tokens"
    elif data.get("out_tokens_total") is not None:
        completion_tokens = int(float(data["out_tokens_total"]))
        evidence = "client_decode_tokens" if completion_tokens > n_requests else "no_decode_tokens"
    else:
        completion_tokens, evidence = None, "unknown_completion_tokens"
    itl = [s.get("itl_p50_s") for s in ok_streams if s.get("itl_p50_s") is not None]
    failed = [s for s in streams if s.get("ok") is False]
    return {"source_path": str(path), "requests": n_requests, "ok_requests": len(ok_streams) or n_requests,
            "failed_streams": failed, "ttft_ms_median": ttft_ms, "tpot_ms_median": tpot_ms,
            "itl_p50_ms_median": _ms(sorted(itl)[len(itl) // 2]) if itl else None,
            "decode_token_count": completion_tokens,
            "metric_semantics": "native_client_harness; tpot_mean_s producer-reported; completion_tokens/chunks producer counts",
            "decode_evidence": evidence, "samples": streams}


def _measured_json_path(directory: Path) -> Path | None:
    """Exact same case/cell native harness record (no neighbor/cell borrowing)."""
    try:
        resolved = directory.resolve()
    except OSError:
        return None
    for ancestor in [resolved, *resolved.parents]:
        if ancestor.name != "out":
            continue
        parts = resolved.relative_to(ancestor).parts
        if len(parts) < 2:
            return None
        case = ancestor / parts[0]
        candidate = case / "measured" / f"{case.name}_{parts[1]}.json"
        return candidate if candidate.is_file() else None
    return None


def _client_from_cell_meta(path: Path) -> dict[str, Any] | None:
    data = _read_json(path)
    if not data:
        return None
    ttft, tpot = data.get("ttft_ms"), data.get("tpot_ms")
    ttft = (ttft or {}).get("median") if isinstance(ttft, Mapping) else ttft
    tpot = (tpot or {}).get("median") if isinstance(tpot, Mapping) else tpot
    if ttft is None and tpot is None:
        return None
    return {"source_path": str(path), "requests": int(data.get("completed") or 0),
            "ok_requests": int(data.get("completed") or 0),
            "ttft_ms_median": float(ttft) if ttft is not None else None,
            "tpot_ms_median": float(tpot) if tpot is not None else None,
            "metric_semantics": "cell_metadata_median; no per-request token boundary",
            "decode_evidence": "cell_metadata_only", "samples": []}


def _source_index() -> dict[str, dict[str, Any]]:
    """One-time recorded-source index for managed suites."""
    if _RESULTS_SOURCE_INDEX:
        return _RESULTS_SOURCE_INDEX
    index = _RESULTS_SOURCE_INDEX
    for phase_name in ("decode", "prefill"):
        for case in (_read_json(RESULTS_DIR / f"{phase_name}.json") or {}).get("cases") or ():
            cid = str(case.get("case_id") or case.get("id") or "")
            source = case.get("source") or {}
            path = str(source.get("path") or source.get("trace_path") or source.get("kernel_details_path") or "")
            if not cid or not path:
                continue
            entry = {"path": path, "sha256": source.get("sha256"), "comparison": case.get("comparison") or {}}
            for key in (f"registered_{phase_name}:{cid}", f"registered_{phase_name}:{cid.split(':', 1)[-1]}"):
                index[key] = entry
    for item in (_read_json(RESULTS_DIR / "dsh_full_generalization.json") or {}).get("heldout_cases") or ():
        path = str(item.get("path") or "")
        if not path:
            continue
        suffix = path
        for root in DATA_ROOTS:
            prefix = str(root).rstrip("/") + "/"
            if path.startswith(prefix):
                suffix = path[len(prefix):]
                break
        index[f"dsh_heldout:{_clean_rel(suffix)}"] = {
            "path": path, "observed_ms": item.get("observed_ms"), "status": item.get("status"),
            "traits": item.get("traits") or {}}
    for item in (_read_json(RESULTS_DIR / "wave5_full_generalization.json") or {}).get("cases") or ():
        path = str(item.get("path") or "")
        if path:
            index[f"wave5:{item.get('hw', '')}:{item.get('cohort', '')}:{item.get('cell', '')}"] = {
                "path": path, "observed_ms": item.get("observed_ms"), "status": item.get("status"),
                "phase": item.get("phase"), "forward_count": item.get("forward_count")}
    return index


def _multinode_index() -> dict[str, Path]:
    global _MULTINODE_INDEX
    if _MULTINODE_INDEX is not None:
        return _MULTINODE_INDEX
    index: dict[str, Path] = {}
    if MULTINODE_RUNS_ROOT.exists():
        for case in MULTINODE_RUNS_ROOT.iterdir():
            if not case.is_dir():
                continue
            for cell in case.iterdir():
                if not cell.is_dir():
                    continue
                index[f"{case.name}:{cell.name}"] = cell
                idle = cell / "idle_dp_rank"
                if idle.is_dir():
                    index[f"{case.name}:{cell.name}:idle_dp_rank"] = idle
    _MULTINODE_INDEX = index
    return index


def resolve_capture_directory(row: Mapping[str, Any]) -> tuple[Path | None, Path | None, list[str]]:
    """Direct same-capture resolution; row-supplied paths are never trusted."""
    cid = str(row.get("capture_id") or "")
    base = _base_capture_id(cid)
    suite = str(row.get("suite") or (base.split(":", 1)[0] if ":" in base else ""))
    notes: list[str] = []
    if suite.startswith("a5_multinode") or base.startswith("a5_multinode"):
        cell_key = ":".join(base.split(":")[1:])
        cell = _multinode_index().get(cell_key)
        if cell is not None:
            return cell, None, notes
        return None, None, [f"multinode cell not indexed: {cell_key}"]
    entry = _source_index().get(base)
    if entry:
        source = Path(str(entry["path"]))
        if source.exists():
            return (source.parent if source.is_file() else source), (source if source.is_file() else None), notes
        recovered = _recovered_source(source)
        if recovered is not None:
            return recovered.parent, recovered, [f"recovered same-bytes source for {source}"]
        return None, None, [f"recorded source missing: {source}"]
    rel = base.split(":", 1)[1] if ":" in base else base
    if not rel:
        return None, None, ["empty capture path"]
    for root in DATA_ROOTS:
        direct = root / rel
        candidates = [direct, direct / "kernel_details.csv", direct / "kernel_details.csv.gz"]
        if "/node/" in str(direct):
            import glob
            candidates.extend(Path(m) for m in glob.glob(str(direct).replace("/node/", "/*/")))
        for candidate in candidates:
            if candidate.is_file() or candidate.is_dir():
                return (candidate.parent if candidate.is_file() else candidate), (candidate if candidate.is_file() else None), notes
    if rel.endswith((".csv", ".gz")):
        parent = Path(rel).parent
        for root in DATA_ROOTS:
            if (root / parent).is_dir():
                return root / parent, None, notes
    return None, None, [f"no capture directory for {rel}"]


def _artifact_in_dir(directory: Path, names: Sequence[str], preferred: Path | None = None) -> Path | None:
    if preferred is not None and preferred.parent == directory and preferred.is_file():
        return preferred
    for name in names:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    if any(("kernel" in name or "op_summary" in name) for name in names):
        for pattern in ("*.kernel_details.csv.gz", "*.kernel_details.csv", "op_summary_*.csv.gz", "op_summary_*.csv"):
            matches = sorted(directory.glob(pattern))
            if matches:
                return matches[0]
    return None


def _declared_steps(row: Mapping[str, Any]) -> int | None:
    try:
        value = int(row.get("forward_steps"))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _row_summary_is_derived(ks: Mapping[str, Any], observed_ms: float | None, steps: int) -> bool:
    try:
        total = float(ks.get("total_kernel_duration_us") or 0.0)
    except (TypeError, ValueError):
        return False
    return bool(observed_ms and total > 0.0 and steps > 0
                and abs(total - float(observed_ms) * steps * 1000.0) <= max(0.05, 1e-9 * float(observed_ms) * steps * 1000.0))


def _same_source(directory: Path | None, raw_path: Path | None, reported: Path,
                 reported_sha: str | None) -> tuple[bool, bool]:
    """(same_capture, same_artifact) using path + streamed digest identity."""
    if raw_path is not None:
        try:
            if reported.resolve() == raw_path.resolve():
                if reported_sha:
                    digest = _sha256_file(raw_path)
                    if digest is not None and digest != reported_sha.lower():
                        return False, False
                return True, True
        except OSError:
            pass
        recovered = _recovered_source(reported)
        if recovered is not None and raw_path is not None:
            try:
                if recovered.resolve() == raw_path.resolve():
                    return True, True
            except OSError:
                pass
    same_capture = False
    if directory is not None:
        try:
            d, r = directory.resolve(), reported.resolve()
            same_capture = d == r or d in r.parents
        except OSError:
            pass
    if same_capture and reported_sha and raw_path is not None:
        if _sha256_file(raw_path) == reported_sha.lower():
            return True, True
    return same_capture, False


def _reported_entry(entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not entry:
        return None
    comparison = entry.get("comparison") or {}
    observed = comparison.get("observed_ms", entry.get("observed_ms"))
    if isinstance(observed, Mapping):
        observed = observed.get("mean", observed.get("p50"))
    traits = entry.get("traits") or {}
    return {"observed_ms": observed, "path": entry.get("path"), "sha256": entry.get("sha256"),
            "comparison_status": comparison.get("status", entry.get("status")),
            "metric_boundary": comparison.get("metric_boundary"), "scope": comparison.get("scope"),
            "endpoints": comparison.get("endpoints") or {},
            "observed_forward_count": comparison.get("observed_forward_count") or entry.get("forward_count"),
            "phase": entry.get("phase") or traits.get("phase")}


def _reported_scope(entry: Mapping[str, Any] | None, raw_path: Path | None,
                    directory: Path | None, phase: str) -> dict[str, Any]:
    """Producer-reported forward-span field, validated by status/phase/source identity."""
    if not entry:
        return {"status": "unknown", "reason": "no recorded comparison entry"}
    path = Path(str(entry.get("path") or ""))
    status = entry.get("comparison_status")
    if status is not None and str(status) != "compared":
        return {"status": "unknown", "reason": f"recorded comparison status {status!r}", "source_path": str(path)}
    recorded_phase = str(entry.get("phase") or "").lower()
    if recorded_phase and phase and recorded_phase != phase:
        return {"status": "unknown", "reason": "recorded phase does not match row phase", "source_path": str(path)}
    observed = entry.get("observed_ms")
    if observed is None:
        return {"status": "unknown", "reason": "no recorded observed_ms", "source_path": str(path)}
    same_capture, same_artifact = _same_source(directory, raw_path, path, entry.get("sha256"))
    if not same_capture:
        return {"status": "unknown", "reason": "recorded source does not match resolved capture/rank/window",
                "source_path": str(path)}
    return {"status": "reported", "boundary": "producer_reported_device_forward_span",
            "observed_ms": round(float(observed), 9), "source_path": str(path),
            "source_sha256": entry.get("sha256"), "same_artifact": same_artifact,
            "source_relation": "same_artifact" if same_artifact else "same_capture_recorded_rank_file",
            "metric_boundary": entry.get("metric_boundary") or "recorded_results",
            "comparison_scope": entry.get("scope"), "endpoints": entry.get("endpoints") or {},
            "observed_forward_count": entry.get("observed_forward_count"),
            "target_proven": bool(entry.get("metric_boundary") or entry.get("endpoints") or entry.get("observed_forward_count")),
            "note": "recorded producer field on its own boundary; not raw additive kernel mass"}


def _forward_window_path() -> Path | None:
    import os
    raw = os.environ.get("MINDIE_FLEET_FORWARD_WINDOWS")
    return Path(raw) if raw else _FORWARD_WINDOW_PATH


def _forward_window_index() -> dict[str, dict[str, Any]]:
    """Index recorded per-forward windows by exact kernel path (peer recovery map)."""
    global _FORWARD_WINDOW_INDEX
    if _FORWARD_WINDOW_INDEX is not None:
        return _FORWARD_WINDOW_INDEX
    index: dict[str, dict[str, Any]] = {}
    path = _forward_window_path()
    if path is not None and path.is_file():
        with path.open("rt", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(item, Mapping) or item.get("error") or not item.get("kernel"):
                    continue
                steps = [s for s in (item.get("steps") or ()) if isinstance(s, Mapping)]
                if not steps:
                    continue
                try:
                    key = str(Path(str(item["kernel"])).resolve())
                except OSError:
                    continue
                index[key] = {"portable_steps": int(item.get("portable_steps") or len(steps)),
                              "offset": item.get("offset"), "portable_match": item.get("portable_match"),
                              "kernel": str(item["kernel"]), "steps": steps}
    _FORWARD_WINDOW_INDEX = index
    return index


def _forward_scope(directory: Path | None) -> dict[str, Any]:
    """Per-forward window class sums only from an exact recorded kernel match."""
    if _forward_window_path() is None:
        return {"status": "unknown", "reason": "no recorded per-forward window map configured"}
    if directory is None:
        return {"status": "unknown", "reason": "no resolved capture directory"}
    try:
        key = str(directory.resolve())
    except OSError:
        return {"status": "unknown", "reason": "unresolvable capture directory"}
    index = _forward_window_index()
    candidates = [directory / "kernel_details.csv.gz", directory / "kernel_details.csv"]
    candidates += sorted(directory.glob("*.kernel_details.csv.gz")) + sorted(directory.glob("*.kernel_details.csv"))
    entry = None
    for candidate in candidates:
        try:
            entry = index.get(str(candidate.resolve()))
        except OSError:
            entry = None
        if entry is not None:
            break
    if entry is None:
        return {"status": "unknown", "reason": "no recorded per-forward window for this exact kernel/rank",
                "source_kernel": str(directory)}
    steps = entry["steps"]
    totals: dict[str, float] = {}
    window_totals: list[float] = []
    for step in steps:
        window_total = 0.0
        for name, value in step.items():
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                totals[str(name)] = totals.get(str(name), 0.0) + float(value)
                window_total += float(value)
        window_totals.append(window_total)
    n = len(steps)
    mean_total = sum(totals.values()) / n if n else None
    return {"status": "measured", "boundary": "per_forward_window_additive_class_sum",
            "source_kernel": entry["kernel"], "portable_steps": entry["portable_steps"],
            "offset": entry["offset"], "portable_match": entry["portable_match"],
            "window_count": n,
            "family_total_us": {k: round(v, 6) for k, v in sorted(totals.items())},
            "family_mean_us_per_window": {k: round(v / n, 6) for k, v in sorted(totals.items())} if n else {},
            "mean_additive_us_per_window": round(mean_total, 6) if mean_total is not None else None,
            "window_additive_us": [round(v, 6) for v in window_totals],
            "samples_ms": [round(v / 1000.0, 9) for v in window_totals],
            "samples_basis": "additive_class_sum_ms",
            "note": "additive class sums inside recorded forward windows; not wall/client latency"}


def _registered_extraction_index() -> dict[tuple[str, str], Path]:
    global _REGISTERED_EXTRACTION_INDEX
    if _REGISTERED_EXTRACTION_INDEX is not None:
        return _REGISTERED_EXTRACTION_INDEX
    index: dict[tuple[str, str], Path] = {}
    data = _read_json(CASES_PATH) or {}
    for case in data.get("cases") or ():
        if not isinstance(case, Mapping) or not case.get("extraction_path"):
            continue
        phase = str(case.get("phase") or "").lower()
        case_id = str(case.get("case_id") or "")
        path = Path(str(case["extraction_path"]))
        if phase and case_id and path.is_file():
            index[(phase, case_id)] = path
    _REGISTERED_EXTRACTION_INDEX = index
    return index


def _receipt_index_path() -> Path | None:
    import os
    raw = os.environ.get("MINDIE_FLEET_RECEIPT_INDEX")
    return Path(raw) if raw else _RECEIPT_INDEX_PATH


def _receipt_index() -> dict[str, dict[str, Any]]:
    """Exact source_path -> measured receipt path from the reviewer index (configurable)."""
    global _RECEIPT_INDEX
    if _RECEIPT_INDEX is not None:
        return _RECEIPT_INDEX
    index: dict[str, dict[str, Any]] = {}
    path = _receipt_index_path()
    if path is None:
        from fleet_source_discovery import canonical_receipts_by_source
        for source, records in canonical_receipts_by_source().items():
            signatures = {(r.get("source_sha256"), r.get("source_size_bytes")) for r in records}
            if len(signatures) > 1:
                continue  # preserve conflict as unknown; never pick by timing/usable count
            record = min(records, key=lambda r: str(r.get("receipt") or ""))
            index[source] = {"receipt": Path(record["receipt"]),
                             "sha256": record.get("source_sha256"),
                             "size_bytes": record.get("source_size_bytes")}
        _RECEIPT_INDEX = index
        return index
    if path is not None and path.is_file():
        with path.open("rt", encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if str(row.get("source_receipt_status") or "") != "measured":
                    continue
                if int(row.get("usable_window_count") or 0) <= 0:
                    continue
                if str(row.get("size_match") or "").lower() not in {"", "true", "1"}:
                    continue
                source, receipt = str(row.get("source_path") or ""), str(row.get("receipt") or "")
                if not source or not receipt or not Path(receipt).is_file():
                    continue
                record = {"receipt": Path(receipt), "sha256": row.get("source_sha256")}
                # Duplicate parser/cache receipts agree on the window signature;
                # choose lexicographically, never by error/duration.
                current = index.get(source)
                if current is None or receipt < str(current["receipt"]):
                    index[source] = record
    _RECEIPT_INDEX = index
    return index


def _identity(directory: Path | None, export: Mapping[str, Any] | None) -> dict[str, Any]:
    ident: dict[str, Any] = {"directory": str(directory) if directory else "", "rank_id": None,
                             "worker_dir": None, "rank_label": None, "rank_selection": None}
    if directory is not None:
        ident["rank_selection"] = "idle_dp_rank" if directory.name == "idle_dp_rank" else "direct"
        for candidate in sorted(directory.glob("profiler_info_*.json")):
            data = _read_json(candidate) or {}
            if data.get("rank_id") is not None:
                ident["rank_id"], ident["rank_id_source"] = data["rank_id"], str(candidate)
                break
    if export:
        ident["worker_dir"] = export.get("worker_dir")
        ident["rank_label"] = export.get("rank_label")
    elif directory is not None and not ident.get("worker_dir"):
        ident["worker_dir"] = directory.name
        ident["worker_parent"] = directory.parent.name
    return ident


def _cell_meta_path(directory: Path) -> Path | None:
    candidate = directory.parent / f"{directory.name}.json"
    return candidate if candidate.is_file() else None


