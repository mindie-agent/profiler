"""Reusable inventory of captured kernel variants and observed device costs.

[Role]
  Stream existing CANN CSV/gzip/tar exports into an incremental SQLite inventory.
  Keep exact multi-input/output signatures and capture/rank context, then expose
  observed duration distributions without inventing an analytic baseline.
[Invariants]
  Raw sources are read-only. Copied event occurrences are idempotent. A capture's
  repeated calls are observations, not independent measurement trials. Missing
  shapes, SKU or execution context remain explicit gaps. Profiled durations are
  never relabelled isolated kernel service, dispatch, or train-only validation.
[Timeouts & Locks]
  One streaming reader; batches of 4096 rows; SQLite WAL/busy_timeout=5000,
  32 MiB cache and disk-backed sorting. Per-source scan timeout is explicit.
[Side-Effect Policy]
  Writes only the requested inventory DB and bounded summary/JSONL exports.
  Does not launch devices, SSH, services, capture tools or calibration jobs.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import re
import sqlite3
import tarfile
import time
from contextlib import closing, contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator, Mapping, TextIO

from .events import ProfilerQueryError, ProfilerSchemaError
from .sources_db import load_mapping


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> bytes:
    return hashlib.blake2b(_json(value).encode(), digest_size=16).digest()


def _text(value: Any) -> str:
    text = str(value or "").strip().strip('"').strip()
    return "" if text.upper() in {"N/A", "NA", "NONE", "NULL"} else text


def _ns(value: str, label: str) -> int:
    try:
        result = Decimal(value.strip()) * 1000
        if not result.is_finite():
            raise InvalidOperation
        return int(result.to_integral_value())
    except (InvalidOperation, ValueError) as exc:
        raise ProfilerSchemaError(f"kernel inventory: invalid {label}: {value!r}") from exc


def _signature(value: str) -> str:
    # Preserve optional argument slots and all tensor dimensions. This is not a
    # first-input-only shape or a lossy name-based operator-family guess.
    return re.sub(r"\s+", "", _text(value))


def csv_rows(handle: TextIO) -> Iterator[dict[str, str]]:
    """Read the two real CANN export vocabularies through shared CSV aliases."""
    aliases = dict(load_mapping()["csv"]["aliases"])
    aliases.update({
        "name": ["kernel_name", *aliases["name"]],
        "start_us": ["task_start(us)", "Task Start Time(us)", *aliases["start_us"]],
        "duration_us": ["task_time(us)", "Task Duration(us)", *aliases["duration_us"]],
        "type": ["OP Type", "kernel_type", *aliases["type"]],
        "core": ["kernel_type", *aliases["core"]],
        "output_shapes": ["Output Shapes"], "output_dtypes": ["Output Data Types"],
        "output_formats": ["Output Formats"],
    })
    reader = csv.DictReader(handle)
    columns = {str(key).strip().lower(): key for key in reader.fieldnames or ()}
    selected = {
        field: next((columns[a.lower()] for a in names if a.lower() in columns), None)
        for field, names in aliases.items()
    }
    if any(selected.get(key) is None for key in ("name", "start_us", "duration_us")):
        raise ProfilerSchemaError("kernel inventory: CSV lacks name/start/duration columns")
    for row in reader:
        yield {key: _text(row.get(column)) if column else "" for key, column in selected.items()}


def is_kernel_csv(name: str) -> bool:
    base = Path(name).name
    return any(token in base for token in ("kernel_details", "op_summary", "task_time")) and base.endswith((".csv", ".csv.gz"))


def _has_rich_export(path: Path) -> bool:
    return any(path.parent.glob("*kernel_details*.csv*")) or any(path.parent.glob("*op_summary*.csv*"))


def discover(roots: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for root in roots:
        path = Path(root).resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        candidates = (path,) if path.is_file() else path.rglob("*")
        for candidate in candidates:
            if "task_time" in candidate.name and _has_rich_export(candidate):
                continue
            if candidate.is_file() and (is_kernel_csv(candidate.name) or candidate.name.endswith((".tgz", ".tar.gz"))):
                paths.add(candidate.resolve())
    return sorted(paths)


@contextmanager
def _csv_handle(stream: Any, name: str):
    binary = gzip.GzipFile(fileobj=stream) if name.endswith(".gz") else stream
    text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
    try:
        yield text
    finally:
        text.close()


def source_streams(path: Path):
    if is_kernel_csv(path.name):
        with path.open("rb") as binary, _csv_handle(binary, path.name) as handle:
            yield "", handle
    else:
        # Seekable tar mode supports TextIOWrapper on extractfile without
        # extracting files or loading member payloads into memory.
        with tarfile.open(path, "r:gz") as archive:
            fallback = []
            rich_directories = set()
            for member in archive:
                if member.isfile() and is_kernel_csv(member.name):
                    if "task_time" in member.name:
                        fallback.append(member)
                        continue
                    rich_directories.add(str(Path(member.name).parent))
                    binary = archive.extractfile(member)
                    with _csv_handle(binary, member.name) as handle:
                        yield member.name, handle
            for member in fallback:
                if str(Path(member.name).parent) not in rich_directories:
                    with _csv_handle(archive.extractfile(member), member.name) as handle:
                        yield member.name, handle


def _context(path: Path, rules: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for rule in sorted(rules, key=lambda r: len(r["prefix"])):
        if path.is_relative_to(Path(rule["prefix"]).resolve()):
            result.update(rule["context"])
    return result


def _capture(path: Path, member: str, context: Mapping[str, Any]) -> str:
    source = member or str(path)
    cell = re.search(r"(?:^|/)(?:prof_)?(p\d+[_-]c\d+[^/]*|r\d+_rank\d+)(?:/|$)", source)
    if cell:
        return str(context.get("capture_group") or path.parent) + "/" + cell.group(1)
    native = re.search(r"PROF_[^/]+", source)
    if native:
        return native.group()
    # The context explicitly identifies the campaign; the raw timestamp/device
    # identity deduplicates copies inside and outside an archive in that scope.
    return str(context.get("capture_group") or path.parent)


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=5000")
    connection.execute("PRAGMA cache_size=-32768")
    connection.execute("PRAGMA temp_store=FILE")
    has_memberships = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='event_sources'"
    ).fetchone() is not None
    connection.executescript("""
      CREATE TABLE IF NOT EXISTS sources(
        id INTEGER PRIMARY KEY, path TEXT, member TEXT, size INTEGER, mtime INTEGER,
        status TEXT, rows INTEGER DEFAULT 0, inserted INTEGER DEFAULT 0,
        nonpositive INTEGER DEFAULT 0, error TEXT,
        context TEXT, UNIQUE(path,member));
      CREATE TABLE IF NOT EXISTS variants(
        id BLOB PRIMARY KEY, signature TEXT NOT NULL, context TEXT NOT NULL,
        capture TEXT NOT NULL, eligible INTEGER NOT NULL, reason TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS events(
        id BLOB PRIMARY KEY, variant BLOB NOT NULL, source INTEGER NOT NULL,
        row_number INTEGER NOT NULL, duration_ns INTEGER NOT NULL) WITHOUT ROWID;
      CREATE TABLE IF NOT EXISTS costs(
        variant BLOB PRIMARY KEY, calls INTEGER, median_ns REAL, mean_ns REAL,
        min_ns INTEGER, max_ns INTEGER) WITHOUT ROWID;
      CREATE TABLE IF NOT EXISTS event_sources(
        event BLOB NOT NULL, source INTEGER NOT NULL, row_number INTEGER NOT NULL,
        PRIMARY KEY(event,source)) WITHOUT ROWID;
      CREATE INDEX IF NOT EXISTS event_sources_source ON event_sources(source);
    """)
    if not has_memberships:
        # The old schema kept only one owner of a copied occurrence. Re-read
        # registered sources to recover real memberships, including sources
        # outside this invocation's roots; do not invent references to copies.
        connection.execute("INSERT OR IGNORE INTO event_sources SELECT id,source,row_number FROM events")
        connection.execute("UPDATE sources SET status='reindex'")
        connection.commit()
    return connection


def _release_source(connection, source_id):
    """Remove one source's observations while preserving successful copies."""
    connection.execute("""
      DELETE FROM events WHERE id IN (SELECT event FROM event_sources WHERE source=?)
      AND NOT EXISTS (SELECT 1 FROM event_sources m JOIN sources s ON s.id=m.source
                      WHERE m.event=events.id AND m.source!=? AND s.status='completed')
    """, (source_id, source_id))
    connection.execute("""
      UPDATE events SET (source,row_number)=(
        SELECT m.source,m.row_number FROM event_sources m JOIN sources s ON s.id=m.source
        WHERE m.event=events.id AND m.source!=? AND s.status='completed'
        ORDER BY m.source LIMIT 1)
      WHERE source=?
    """, (source_id, source_id))
    connection.execute("DELETE FROM event_sources WHERE source=?", (source_id,))


def _reasons(signature: Mapping[str, str], context: Mapping[str, Any]) -> list[str]:
    reasons = []
    for key in ("name", "input_shapes", "input_dtypes", "input_formats"):
        if not signature[key]:
            reasons.append(f"missing_{key}")
    for key in ("hardware_key", "environment_key"):
        if not context.get(key):
            reasons.append(f"missing_{key}")
    kind = " ".join(signature[key] for key in ("core", "name", "type")).upper()
    if any(token in kind for token in ("CPU", "HCCL", "HCOM")):
        reasons.append("communication_or_aicpu_use_existing_transport_model")
    if any(token in kind for token in ("MEMCPY", "MEMSET")):
        reasons.append("memory_task_use_existing_transfer_model")
    if context.get("split") == "heldout":
        reasons.append("heldout_not_for_calibration")
    if context.get("calibration_excluded_reason"):
        reasons.append(str(context["calibration_excluded_reason"]))
    return reasons


def _event(row: dict[str, str], context: dict[str, Any], capture: str):
    start = _ns(row["start_us"], "start_us")
    duration = _ns(row["duration_us"], "duration_us")
    if duration <= 0:
        return None
    signature = {key: _signature(row.get(key, "")) for key in (
        "name", "type", "core", "block_dim", "mix_block_dim",
        "input_shapes", "input_dtypes", "input_formats",
        "output_shapes", "output_dtypes", "output_formats",
    )}
    signature["device_id"] = row["device_id"]
    reasons = _reasons(signature, context)
    identity = {"signature": signature, "context": context, "capture": capture}
    variant = _digest(identity)
    occurrence = _digest([variant.hex(), start, duration, row["stream_id"], row["task_id"], row["context_id"]])
    return variant, occurrence, duration, signature, reasons


def ingest_source(connection, path: Path, member: str, handle: TextIO,
                  context: dict[str, Any], *, timeout_s: float) -> dict[str, Any]:
    stat = path.stat()
    previous = connection.execute(
        "SELECT id,size,mtime,status,rows,inserted,context FROM sources WHERE path=? AND member=?",
        (str(path), member),
    ).fetchone()
    if (previous and previous[1:4] == (stat.st_size, stat.st_mtime_ns, "completed")
            and previous[6] == _json(context)):
        return {"path": str(path), "member": member, "status": "reused", "rows": previous[4]}
    if previous:
        _release_source(connection, previous[0])
    connection.execute(
        "INSERT INTO sources(path,member,size,mtime,status,context) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(path,member) DO UPDATE SET status='reading',error=NULL,context=excluded.context",
        (str(path), member, stat.st_size, stat.st_mtime_ns, "reading", _json(context)),
    )
    source_id = connection.execute("SELECT id FROM sources WHERE path=? AND member=?", (str(path), member)).fetchone()[0]
    capture = _capture(path, member, context)
    count = inserted = nonpositive = 0
    batch = []
    known: set[bytes] = set()
    deadline = time.monotonic() + timeout_s

    def flush():
        nonlocal inserted
        before = connection.total_changes
        connection.executemany("INSERT OR IGNORE INTO events VALUES(?,?,?,?,?)", batch)
        inserted += connection.total_changes - before
        connection.executemany("INSERT OR IGNORE INTO event_sources VALUES(?,?,?)",
                               ((row[0], row[2], row[3]) for row in batch))
        batch.clear()
        connection.commit()

    try:
        for count, row in enumerate(csv_rows(handle), 1):
            if count % 4096 == 1 and time.monotonic() > deadline:
                raise ProfilerQueryError(f"kernel inventory: source exceeded {timeout_s:g}s")
            event = _event(row, context, capture)
            if event is None:
                nonpositive += 1
                continue
            variant, occurrence, duration, signature, reasons = event
            if variant not in known:
                connection.execute("INSERT OR IGNORE INTO variants VALUES(?,?,?,?,?,?)", (
                    variant, _json(signature), _json(context), capture, not reasons, ";".join(reasons),
                ))
                known.add(variant)
                if len(known) >= 4096:
                    known.clear()
            batch.append((occurrence, variant, source_id, count, duration))
            if len(batch) >= 4096:
                flush()
        flush()
        if path.stat().st_size != stat.st_size or path.stat().st_mtime_ns != stat.st_mtime_ns:
            raise ProfilerQueryError("kernel inventory: source changed during read; retry after capture settles")
        connection.execute("UPDATE sources SET status='completed',size=?,mtime=?,rows=?,inserted=?,nonpositive=? WHERE id=?", (
            stat.st_size, stat.st_mtime_ns, count, inserted, nonpositive, source_id,
        ))
        connection.commit()
    except Exception as exc:
        # Failed partial imports must not leak through raw catalogue readers.
        # Successful copies retain their measured occurrences.
        _release_source(connection, source_id)
        connection.execute("UPDATE sources SET status='failed',error=? WHERE id=?", (str(exc), source_id))
        connection.commit()
        raise
    return {"path": str(path), "member": member, "status": "completed", "rows": count, "inserted": inserted}


def summarize(connection, output: Path) -> dict[str, Any]:
    connection.execute("CREATE INDEX IF NOT EXISTS events_variant_duration ON events(variant,duration_ns)")
    connection.execute("DELETE FROM costs")
    connection.execute("""
      INSERT INTO costs
      WITH ranked AS (
        SELECT e.variant,e.duration_ns,
          ROW_NUMBER() OVER(PARTITION BY e.variant ORDER BY e.duration_ns) AS r,
          COUNT(*) OVER(PARTITION BY e.variant) AS n
        FROM events e JOIN sources s ON s.id=e.source WHERE s.status='completed'
      ), medians AS (
        SELECT variant,AVG(duration_ns) AS median_ns FROM ranked
        WHERE r IN ((n+1)/2,(n+2)/2) GROUP BY variant
      ), aggregates AS (
        SELECT e.variant,COUNT(*) n,AVG(e.duration_ns) mean_ns,MIN(e.duration_ns) lo,MAX(e.duration_ns) hi
        FROM events e JOIN sources s ON s.id=e.source WHERE s.status='completed' GROUP BY e.variant
      ) SELECT a.variant,a.n,m.median_ns,a.mean_ns,a.lo,a.hi
        FROM aggregates a JOIN medians m ON a.variant=m.variant
    """)
    connection.commit()
    counts = {"variants": 0, "cost_variants": 0, "gap_variants": 0, "calls": 0}
    reasons: dict[str, int] = {}
    with (output / "variants.jsonl").open("w", encoding="utf-8") as variants, (output / "missing.jsonl").open("w", encoding="utf-8") as gaps:
        for key, signature, context, capture, eligible, reason, calls, med, mean, lo, hi in connection.execute(
            "SELECT v.*,c.calls,c.median_ns,c.mean_ns,c.min_ns,c.max_ns FROM variants v JOIN costs c ON v.id=c.variant ORDER BY v.id"
        ):
            signature, context = json.loads(signature), json.loads(context)
            current_reason = ";".join(_reasons(signature, context))
            if current_reason != reason:
                eligible, reason = not current_reason, current_reason
                connection.execute("UPDATE variants SET eligible=?,reason=? WHERE id=?", (eligible, reason, key))
            counts["variants"] += 1
            counts["calls"] += calls
            counts["cost_variants" if eligible else "gap_variants"] += 1
            row = {"variant_id": key.hex(), "signature": signature, "context": context,
                   "capture": capture, "calls": calls, "median_ns": med, "mean_ns": mean, "min_ns": lo,
                   "max_ns": hi, "source_class": "observed", "timing_scope": "profiled_device_kernel",
                   "eligible": bool(eligible), "reason": reason, "independent_trials": None}
            variants.write(_json(row) + "\n")
            if reason:
                for item in reason.split(";"):
                    reasons[item] = reasons.get(item, 0) + 1
                row["next_action"] = "reuse_existing_source_metadata_or_transport_artifact"
                row["collect_again"] = False
                gaps.write(_json(row) + "\n")
    connection.commit()
    counts["gap_reasons"] = reasons
    counts["source_status"] = dict(connection.execute("SELECT status,COUNT(*) FROM sources GROUP BY status"))
    counts["raw_rows"] = connection.execute("SELECT COALESCE(SUM(rows),0) FROM sources WHERE status='completed'").fetchone()[0]
    counts["nonpositive_rows"] = connection.execute("SELECT COALESCE(SUM(nonpositive),0) FROM sources WHERE status='completed'").fetchone()[0]
    counts["duplicate_rows"] = counts["raw_rows"] - counts["nonpositive_rows"] - counts["calls"]
    return counts


def build_inventory(manifest: Mapping[str, Any], output: str | Path, *, timeout_s: float = 300) -> dict[str, Any]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = discover(list(manifest["roots"]))
    db = output / "kernels.sqlite"
    failures = []
    no_exports = []
    source_actions = {"completed": 0, "reused": 0}
    with closing(_connect(db)) as connection:
        registered = {
            Path(path): json.loads(context) for path, context in connection.execute(
                "SELECT path,context FROM sources WHERE status='reindex' ORDER BY id")
        }
        current = set(paths)
        paths = sorted(current | registered.keys())
        for index, path in enumerate(paths, 1):
            found = 0
            members = set()
            context = (_context(path, list(manifest.get("contexts", [])))
                       if path in current else registered[path])
            try:
                for member, handle in source_streams(path):
                    found += 1
                    members.add(member)
                    result = ingest_source(connection, path, member, handle, context, timeout_s=timeout_s)
                    source_actions[result["status"]] += 1
                # Only a successful complete archive enumeration proves a
                # previous member was removed. Narrower roots are incremental.
                for source_id, member in connection.execute(
                        "SELECT id,member FROM sources WHERE path=?", (str(path),)).fetchall():
                    if member not in members:
                        _release_source(connection, source_id)
                        connection.execute("UPDATE sources SET status='removed' WHERE id=?", (source_id,))
                connection.commit()
                if not found:
                    no_exports.append(str(path))
            except (OSError, EOFError, tarfile.TarError, ProfilerSchemaError, ProfilerQueryError) as exc:
                failures.append({"source": str(path), "error": str(exc)})
                # Opening/enumerating a source can fail before ingest_source.
                # Invalidate its stale members as well as any partial import.
                for (source_id,) in connection.execute(
                        "SELECT id FROM sources WHERE path=?", (str(path),)).fetchall():
                    _release_source(connection, source_id)
                    connection.execute("UPDATE sources SET status='failed',error=? WHERE id=?",
                                       (str(exc), source_id))
                connection.commit()
            print(f"inventory {index}/{len(paths)} {path.name}: {found} CSV export(s)", flush=True)
        summary = summarize(connection, output)
    summary.update({"db": str(db.resolve()), "source_files": len(paths), "failures": failures,
                    "source_actions": source_actions,
                    "archives_without_kernel_csv": no_exports, "existing_calibrations": manifest.get("existing_calibrations", []),
                    "npu_jobs_started": 0, "measurement_scope": "observed captured kernel duration; host launch excluded"})
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
