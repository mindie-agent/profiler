"""Read-only Ascend profiler SQLite schema probing and bounded window streaming (sources_db_schema).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting read-only ascend profiler sqlite schema probing and bounded window streaming.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import functools
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote
from .events import (
    ClockDomain,
    Event,
    ProfilerQueryError,
    ProfilerSchemaError,
    QueryStats,
    Window,
)

MAPPING_PATH = Path(__file__).resolve().parent / "knowledge" / "db_source_mapping.json"

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_PMU_BUDGET_MIN = 100_000

_PMU_BUDGET_MAX = 2_000_000

_PMU_BUDGET_FACTOR = 8

_TASK_NS_CLOCK = ClockDomain(
    domain="db_task_ns",
    unit="ns",
    scale_ns=1,
    offset_ns=None,
    reference_domain=None,
    source=(
        "TASK.startNs/endNs are nanoseconds per "
        "db_source_mapping.time_units.database; the exporter supplies no "
        "cross-rank synchronization anchor and timestamp magnitude alone does "
        "not establish a shared reference"
    ),
)

def _task_clock() -> ClockDomain:
    """Return the shared TASK ns unit/domain record.

    No reference or offset is attached: the exporter does not supply a
    synchronization anchor, and epoch-looking values from independent hosts
    can still differ.  Sharing the immutable record avoids per-row allocation.
    """
    return _TASK_NS_CLOCK

@functools.lru_cache(maxsize=1)
def load_mapping(path: str | Path | None = None) -> dict[str, Any]:
    mapping_path = Path(path) if path is not None else MAPPING_PATH
    try:
        doc = json.loads(mapping_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProfilerSchemaError(f"db source mapping missing: {mapping_path}") from exc
    except json.JSONDecodeError as exc:
        raise ProfilerSchemaError(f"{mapping_path.name}: invalid JSON: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ProfilerSchemaError(f"{mapping_path.name}: version must be 1")
    for table, columns in doc.get("db_columns", {}).items():
        if not table.endswith("_required"):
            continue
        if not isinstance(columns, list) or not all(_IDENTIFIER.match(str(c)) for c in columns):
            raise ProfilerSchemaError(f"{mapping_path.name}: bad column list {table}")
    pmu_metrics = doc.get("pmu_metrics")
    if not isinstance(pmu_metrics, dict) or not pmu_metrics:
        raise ProfilerSchemaError(f"{mapping_path.name}: pmu_metrics must be a non-empty mapping")
    for name, spec in pmu_metrics.items():
        if not isinstance(spec, dict) or not isinstance(spec.get("db_metric"), str) or not spec["db_metric"]:
            raise ProfilerSchemaError(f"{mapping_path.name}: pmu_metrics.{name} needs db_metric")
        if not isinstance(spec.get("unit"), str) or not spec["unit"]:
            raise ProfilerSchemaError(f"{mapping_path.name}: pmu_metrics.{name} needs unit")
        if "csv_column" in spec and not isinstance(spec["csv_column"], str):
            raise ProfilerSchemaError(f"{mapping_path.name}: pmu_metrics.{name}.csv_column must be a string")
        if "csv_scale" in spec and not isinstance(spec["csv_scale"], (int, float)):
            raise ProfilerSchemaError(f"{mapping_path.name}: pmu_metrics.{name}.csv_scale must be numeric")
    return doc

def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

@dataclass(frozen=True, slots=True)
class DbSchema:
    path: str
    schema_version: str
    schema_variant: str
    tables: tuple[str, ...]
    optional_missing: tuple[str, ...]
    block_column: str | None
    mix_block_column: str | None
    shape_columns: tuple[str, ...]
    wait_column: str | None
    pmu_table_present: bool
    pmu_metric_count: int
    has_wait_ns: bool
    size_bytes: int

    @property
    def exporter_schema_version(self) -> str:
        if self.schema_version == "unversioned":
            return "torch_npu_db_unversioned"
        return f"torch_npu_db_v{self.schema_version}"

    @property
    def source_kind(self) -> str:
        return "ascend_pytorch_profiler_db"

def _connect(path: Path, timeout_s: float) -> sqlite3.Connection:
    if not path.is_file():
        raise ProfilerQueryError(f"profiler db not found: {path}")
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    busy_timeout_s = max(3.0, float(timeout_s))
    try:
        con = sqlite3.connect(uri, uri=True, timeout=busy_timeout_s)
    except sqlite3.Error as exc:
        raise ProfilerQueryError(f"cannot open profiler db read-only: {path}: {exc}") from exc
    con.execute("PRAGMA query_only = ON")
    con.execute(f"PRAGMA busy_timeout = {int(busy_timeout_s * 1000)}")
    return con

def _table_names(con: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    if not _IDENTIFIER.match(table):
        raise ProfilerSchemaError(f"unsafe table identifier: {table!r}")
    return {str(row[1]) for row in con.execute(f"PRAGMA table_info({table})")}

def _first_present(columns: set[str], aliases: list[str]) -> str | None:
    for alias in aliases:
        if alias in columns:
            return alias
    return None

def _missing_columns(columns: set[str], required: list[str]) -> list[str]:
    return [column for column in required if column not in columns]

def _resolve_strings(con: sqlite3.Connection, table: str) -> dict[int, str]:
    try:
        return {int(row[0]): str(row[1]) if row[1] is not None else "" for row in con.execute(f"SELECT id, value FROM {table}")}
    except sqlite3.Error as exc:
        raise ProfilerSchemaError(f"cannot read {table}: {exc}") from exc

def _text(strings: Mapping[int, str], value: Any, unresolved: list[int]) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            key = int(value)
        except ValueError:
            return value
    else:
        try:
            key = int(value)
        except (TypeError, ValueError):
            return ""
    resolved = strings.get(key)
    if resolved is None:
        unresolved.append(key)
        return f"<unresolved:{key}>"
    return resolved

def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _as_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def _as_text(value: Any) -> str:
    return "" if value is None else str(value)

def _source_id_for_file(path: str | Path, size_bytes: int) -> str:
    digest = hashlib.sha256(f"{Path(path).resolve()}\x1f{size_bytes}".encode("utf-8")).hexdigest()
    return f"SRC-{digest[:16].upper()}"

def _capture_id_for_file(path: str | Path) -> str:
    source_path = Path(path)
    capture_root = (
        source_path.parent.parent
        if source_path.parent.name == "ASCEND_PROFILER_OUTPUT"
        else source_path.parent
    )
    digest = hashlib.sha256(str(capture_root.resolve()).encode("utf-8")).hexdigest()
    return f"CAP-{digest[:16].upper()}"
