"""Read-only, schema-checked Ascend profiler sqlite source.

[Role]
  Probe the verified torch_npu/CANN sqlite tables, resolve STRING_IDS once,
  and execute bounded read-only window queries that become ``Event`` rows.

[Invariants]
  * The connection is opened with ``mode=ro`` and ``PRAGMA query_only=ON``.
  * Required tables/columns come from ``knowledge/db_source_mapping.json``;
    an absent table/column or unsupported exporter version raises
    ``ProfilerSchemaError`` instead of guessing or emitting zero rows.
  * Column identifiers are validated, table names come from the mapping, and
    all time values are bound parameters.
  * Each query has a wall-clock deadline, a row budget, and a deterministic
    ``ORDER BY``.  Over-budget reads raise; they are never silently truncated.
  * TASK ``startNs``/``endNs`` remain integer nanoseconds in the DB's local
    clock domain; epoch-like magnitudes never imply cross-host synchronization.
  * Missing ``STRING_IDS`` entries become ``<unresolved:id>``, never ``"0"``.
  * ``COMPUTE_TASK_INFO.waitNs`` and ``TASK_PMU_INFO`` bind to an event only
    when ``globalTaskId`` is unique across the full capture; repeated ACLGraph
    task IDs remain group-scoped and are never summed, averaged, or guessed.

[Timeouts & Locks]
  ``query_timeout_s`` (default 20s) bounds both SQLite ``busy_timeout`` and the
  progress handler; connections close in ``finally`` with zero retained locks.

[Side-Effect Policy]
  Read-only filesystem access to the supplied DB; no writes, no network, and
  no data copied off the source machine.
"""
from __future__ import annotations

import functools
import hashlib
import json
import re
import sqlite3
import time
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

from .sources_db_reader import DbSource
from .sources_db_schema import (
    DbSchema, MAPPING_PATH, _IDENTIFIER, _PMU_BUDGET_FACTOR, _PMU_BUDGET_MAX,
    _PMU_BUDGET_MIN, _TASK_NS_CLOCK, _as_int, _as_optional_int, _as_text,
    _capture_id_for_file, _columns, _connect, _first_present, _missing_columns,
    _resolve_strings, _source_id_for_file, _table_names, _task_clock, _text,
    load_mapping, sha256_file,
)

def probe_db(path: str | Path, *, timeout_s: float = 20.0) -> DbSchema:
    """Fail closed unless every required verified column is present."""

    mapping = load_mapping()
    db_path = Path(path)
    con = _connect(db_path, timeout_s)
    try:
        tables = _table_names(con)
        names = mapping["tables"]
        missing: dict[str, list[str]] = {}
        required_by_table = {
            names["task"]: mapping["db_columns"]["task_required"],
            names["compute"]: mapping["db_columns"]["compute_required"],
            names["strings"]: ["id", "value"],
        }
        for table, required in required_by_table.items():
            if table not in tables:
                missing[table] = list(required)
                continue
            absent = _missing_columns(_columns(con, table), required)
            if absent:
                missing[table] = absent
        optional_missing: list[str] = []
        pmu_table_present = False
        for key in ("comm", "comm_sched", "pmu"):
            table = names[key]
            required = mapping["db_columns"][f"{key}_required"]
            if table not in tables:
                optional_missing.append(table)
                continue
            absent = _missing_columns(_columns(con, table), required)
            if absent:
                missing[table] = absent
            elif key == "pmu":
                pmu_table_present = True
        if names["meta"] in tables:
            absent = _missing_columns(_columns(con, names["meta"]), ["name", "value"])
            if absent:
                missing[names["meta"]] = absent
        if missing:
            detail = ", ".join(f"{table}({','.join(cols)})" for table, cols in sorted(missing.items()))
            raise ProfilerSchemaError(f"{db_path.name}: unknown/incomplete profiler schema: missing {detail}")

        version = "unversioned"
        if names["meta"] in tables:
            meta_columns = _columns(con, names["meta"])
            if {"name", "value"} <= meta_columns:
                row = con.execute(
                    f"SELECT value FROM {names['meta']} WHERE name = ? ORDER BY rowid DESC LIMIT 1",
                    ("SCHEMA_VERSION",),
                ).fetchone()
                if row and row[0] not in (None, ""):
                    version = str(row[0]).strip()
        supported = set(mapping["exporter_schema"]["supported_versions"])
        prefixes = tuple(mapping["exporter_schema"]["supported_prefixes"])
        if version != "unversioned" and version not in supported and not version.startswith(prefixes):
            raise ProfilerSchemaError(
                f"{db_path.name}: unsupported exporter SCHEMA_VERSION {version!r}; "
                f"supported={sorted(supported)} prefixes={list(prefixes)}"
            )
        if version == "unversioned" and not mapping["exporter_schema"]["unversioned_columns_verified"]:
            raise ProfilerSchemaError(f"{db_path.name}: META_DATA.SCHEMA_VERSION missing")

        compute_columns = _columns(con, names["compute"])
        aliases = mapping["db_columns"]["compute_alias_groups"]
        block_col = _first_present(compute_columns, aliases["block_dim"])
        mix_col = _first_present(compute_columns, aliases["mix_block_dim"])
        shape_columns = tuple(
            column
            for column in mapping["db_columns"].get("compute_optional", [])
            if column in compute_columns
        )
        wait_column = _first_present(
            compute_columns, list(mapping["db_columns"].get("compute_wait_columns", []))
        )
        wait_ns = wait_column is not None
        variant_bits = [f"v{version}"]
        if "blockDim" in compute_columns:
            variant_bits.append("blockDim")
        elif "blockNum" in compute_columns:
            variant_bits.append("blockNum")
        else:
            variant_bits.append("noBlock")
        if wait_ns:
            variant_bits.append("waitNs")
        if pmu_table_present:
            variant_bits.append("pmu")
        return DbSchema(
            path=str(db_path.resolve()),
            schema_version=version,
            schema_variant="_".join(variant_bits),
            tables=tuple(sorted(tables)),
            optional_missing=tuple(sorted(optional_missing)),
            block_column=block_col,
            mix_block_column=mix_col,
            shape_columns=shape_columns,
            wait_column=wait_column,
            pmu_table_present=pmu_table_present,
            pmu_metric_count=len(mapping["pmu_metrics"]),
            has_wait_ns=wait_ns,
            size_bytes=db_path.stat().st_size,
        )
    except sqlite3.Error as exc:
        raise ProfilerSchemaError(f"{db_path.name}: schema probe failed: {exc}") from exc
    finally:
        con.close()
