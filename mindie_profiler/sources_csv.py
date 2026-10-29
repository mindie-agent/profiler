"""Streaming kernel_details.csv source with verified header resolution.

[Role]
  Probe and stream the classic CANN ``kernel_details.csv`` projection, resolve
  the real 46-column export and its documented aliases, and return events for
  caller-supplied explicit windows.

[Invariants]
  * Header aliases are case-insensitive and come from the mapping file; a
    missing Name/start/duration(or end) column raises ``ProfilerSchemaError``.
  * CSV times are microseconds and are converted once to integer nanoseconds.
    Wait Time(us) becomes wait_ns; aic/aiv time columns become ns PMU values;
    ratios/cycles/percent stay in their native units.
  * The scan is single-pass and bounded by a row budget and wall-clock
    deadline; invalid timing rows are counted, not converted to zero.
  * No step id is fabricated: a CSV row only belongs to a window the caller
    supplied explicitly.

[Timeouts & Locks]
  ``timeout_s`` (default 30s) is checked every 1024 rows; no lock is held.

[Side-Effect Policy]
  Read-only streaming of the supplied CSV; no writes and no network.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from .events import Event, ProfilerQueryError, ProfilerSchemaError, QueryStats, Window
from .sources_db import load_mapping


@dataclass(frozen=True, slots=True)
class CsvSchema:
    path: str
    header: tuple[str, ...]
    header_sha256: str
    columns: Mapping[str, int]
    block_column: str | None
    mix_block_column: str | None
    wait_column: str | None
    pmu_columns: Mapping[str, int]
    pmu_units: Mapping[str, str]
    pmu_scales: Mapping[str, float]
    pmu_missing: tuple[str, ...]
    optional_missing: tuple[str, ...]
    size_bytes: int

    @property
    def schema_version(self) -> str:
        return f"kernel_details_csv_{len(self.header)}col"

    @property
    def schema_variant(self) -> str:
        variant = "csv_" + ("blockDim" if self.block_column == "Block Dim" else "verified_aliases")
        if self.wait_column:
            variant += "_wait"
        if self.pmu_columns:
            variant += "_pmu"
        return variant

    @property
    def source_kind(self) -> str:
        return "kernel_details_csv"


def _fold(value: str) -> str:
    return str(value).strip().lower()


def _resolve(header: list[str], aliases: list[str]) -> int | None:
    columns = {_fold(name): index for index, name in enumerate(header)}
    for alias in aliases:
        if _fold(alias) in columns:
            return columns[_fold(alias)]
    return None


def _header_digest(header: tuple[str, ...]) -> str:
    return hashlib.sha256("\x1f".join(header).encode("utf-8")).hexdigest()


def _open_csv_text(path: Path):
    """Compressed exports use the same decoder and decompressed row locators."""
    if path.name.endswith(".csv.gz"):
        return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
    return path.open("r", encoding="utf-8-sig", newline="")


def probe_csv(path: str | Path, *, mapping: Mapping[str, Any] | None = None) -> CsvSchema:
    mapping = mapping or load_mapping()
    csv_path = Path(path)
    if not csv_path.is_file():
        raise ProfilerSchemaError(f"kernel_details.csv not found: {csv_path}")
    try:
        with _open_csv_text(csv_path) as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
    except TimeoutError:
        raise
    except OSError as exc:
        raise ProfilerSchemaError(f"cannot read {csv_path.name}: {exc}") from exc
    if not header:
        raise ProfilerSchemaError(f"{csv_path.name}: empty CSV (no header)")
    header = tuple(str(name).strip() for name in header)
    aliases = mapping["csv"]["aliases"]
    required = mapping["csv"]["required_fields"]
    columns: dict[str, int] = {}
    missing: list[str] = []
    for logical in required:
        index = _resolve(list(header), aliases[logical])
        if index is None:
            missing.append(f"{logical} ({'/'.join(aliases[logical])})")
        else:
            columns[logical] = index
    if not any(_resolve(list(header), aliases[key]) is not None for key in mapping["csv"]["duration_or_end"]):
        missing.append("duration_us or end_us")
    if missing:
        raise ProfilerSchemaError(f"{csv_path.name}: unknown CSV schema, missing {', '.join(missing)}")
    for logical, alias_list in aliases.items():
        index = _resolve(list(header), alias_list)
        if index is not None:
            columns[logical] = index
    pmu_columns: dict[str, int] = {}
    pmu_units: dict[str, str] = {}
    pmu_scales: dict[str, float] = {}
    pmu_missing: list[str] = []
    for canonical, spec in mapping["pmu_metrics"].items():
        csv_column = spec.get("csv_column")
        if not csv_column:
            continue
        index = _resolve(list(header), [str(csv_column)])
        if index is None:
            pmu_missing.append(canonical)
            continue
        pmu_columns[canonical] = index
        pmu_units[canonical] = str(spec.get("unit", "unknown"))
        pmu_scales[canonical] = float(spec.get("csv_scale", 1.0))
    optional_missing = tuple(
        logical
        for logical in (
            "core", "type", "stream_id", "task_id", "device_id",
            "block_dim", "mix_block_dim", "op_state",
            "input_shapes", "input_dtypes", "input_formats",
            "output_shapes", "output_dtypes", "output_formats", "wait_us",
        )
        if logical not in columns
    )
    if not pmu_columns:
        optional_missing = optional_missing + ("pmu_columns",)
    return CsvSchema(
        path=str(csv_path.resolve()),
        header=header,
        header_sha256=_header_digest(header),
        columns=columns,
        block_column=header[columns["block_dim"]] if "block_dim" in columns else None,
        mix_block_column=header[columns["mix_block_dim"]] if "mix_block_dim" in columns else None,
        wait_column=header[columns["wait_us"]] if "wait_us" in columns else None,
        pmu_columns=pmu_columns,
        pmu_units=pmu_units,
        pmu_scales=pmu_scales,
        pmu_missing=tuple(pmu_missing),
        optional_missing=optional_missing,
        size_bytes=csv_path.stat().st_size,
    )


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return str(row[index]).strip()


def _number(text: str) -> Decimal | None:
    if not text:
        return None
    try:
        value = Decimal(text)
        return value if value.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def _us_to_ns(value: Decimal) -> int:
    return int((value * Decimal(1000)).to_integral_value())


def _optional_int(text: str) -> int | None:
    value = _number(text)
    return int(value) if value is not None and value == value.to_integral_value() else None


def decode_csv_row(row: list[str], row_index: int, schema: CsvSchema, *,
                   rank_id: str, rank_index: int | None, stats: QueryStats,
                   strict: bool = False, include_zero_duration: bool = False) -> Event | None:
    """Decode one exporter row; analysis counts malformed times, raw reads fail."""
    columns = schema.columns

    def invalid_timing():
        stats.bad_rows += 1
        if strict:
            raise ProfilerSchemaError(
                f"{schema.path}: CSV line {row_index + 2} has invalid timing")
        return None

    start_us = _number(_cell(row, columns.get("start_us")))
    duration_us = _number(_cell(row, columns.get("duration_us")))
    if duration_us is None:
        end_us = _number(_cell(row, columns.get("end_us")))
        duration_us = None if end_us is None or start_us is None else end_us - start_us
    if start_us is None or duration_us is None or duration_us < 0:
        return invalid_timing()
    if duration_us == 0 and not include_zero_duration:
        return None
    start_ns = _us_to_ns(start_us)
    end_ns = start_ns + _us_to_ns(duration_us)
    if end_ns <= start_ns and not (include_zero_duration and duration_us == 0):
        return invalid_timing()
    name = _cell(row, columns.get("name"))
    core = _cell(row, columns.get("core"))
    op_type = _cell(row, columns.get("type")) or core
    wait_us = _number(_cell(row, columns.get("wait_us")))
    if schema.wait_column is None:
        wait_ns, wait_status = None, "not_available"
    elif wait_us is None:
        wait_ns, wait_status = None, "absent"
    elif wait_us < 0:
        wait_ns, wait_status = None, "invalid_value"
    else:
        wait_ns, wait_status = _us_to_ns(wait_us), "bound"
    core_key = core.upper().replace(" ", "_")
    pmu_applicable = not (
        "AI_CPU" in core_key
        or "AICPU" in core_key
        or "COMMUNICATION" in core_key
        or "HCCL" in core_key
    )
    pmu: dict[str, float] = {}
    pmu_resolution: dict[str, float] = {}
    if pmu_applicable:
        for canonical, index in schema.pmu_columns.items():
            value = _number(_cell(row, index))
            if value is not None:
                pmu[canonical] = float(value) * schema.pmu_scales[canonical]
                if value.is_finite():
                    pmu_resolution[canonical] = (
                        float(Decimal(1).scaleb(value.as_tuple().exponent))
                        * schema.pmu_scales[canonical]
                    )
    if not schema.pmu_columns:
        pmu_status = "not_available"
    elif not pmu_applicable:
        pmu_status = "not_applicable"
    elif not pmu:
        pmu_status = "absent"
    else:
        pmu_status = "bound"
    event = Event(
        rank_id=rank_id,
        rank_index=rank_index,
        name=name,
        op_type=op_type,
        task_type=core,
        core=core,
        stream_id=_cell(row, columns.get("stream_id")),
        task_id=_cell(row, columns.get("task_id")),
        device_id=_cell(row, columns.get("device_id")),
        start_ns=start_ns,
        end_ns=end_ns,
        source_kind=schema.source_kind,
        table="kernel_details.csv",
        input_shapes=_cell(row, columns.get("input_shapes")),
        input_dtypes=_cell(row, columns.get("input_dtypes")),
        input_formats=_cell(row, columns.get("input_formats")),
        output_shapes=_cell(row, columns.get("output_shapes")),
        output_dtypes=_cell(row, columns.get("output_dtypes")),
        output_formats=_cell(row, columns.get("output_formats")),
        block_dim=_optional_int(_cell(row, columns.get("block_dim"))),
        mix_block_dim=_optional_int(_cell(row, columns.get("mix_block_dim"))),
        op_state=_cell(row, columns.get("op_state")),
        wait_ns=wait_ns,
        wait_status=wait_status,
        wait_source=(schema.wait_column if schema.wait_column else None),
        wait_provenance={
            "table": "kernel_details.csv",
            "column": schema.wait_column,
            "row_index": row_index,
            "status": wait_status,
            "raw_wait_ns": wait_ns,
        },
        pmu=tuple(sorted(pmu.items())),
        pmu_status=pmu_status,
        pmu_source="kernel_details.csv",
        pmu_kind="aicore" if pmu_applicable else "not_applicable",
        pmu_provenance={
            "table": "kernel_details.csv",
            "row_index": row_index,
            "status": pmu_status,
            "raw_rows": len(pmu),
            "metric_count": len(pmu),
            "binding": "per_row",
            "export_resolution": pmu_resolution,
        },
        locator={
            "source": schema.path,
            "table": "kernel_details.csv",
            "row_index": row_index,
            "csv_line": row_index + 2,
            "task_id": _cell(row, columns.get("task_id")),
            "stream_id": _cell(row, columns.get("stream_id")),
            "device_id": _cell(row, columns.get("device_id")),
        },
    )
    return event


class CsvSource:
    """A probed CSV.  Its single pass fills all requested windows."""

    def __init__(self, schema: CsvSchema, *, rank_id: str, rank_index: int | None) -> None:
        self.schema = schema
        self.rank_id = rank_id
        self.rank_index = rank_index

    def iter_events(
        self, *, max_rows: int = 5_000_000, timeout_s: float = 30.0,
        stats: QueryStats | None = None, strict: bool = False,
        include_zero_duration: bool = False,
    ):
        """Stream normalized events without retaining the full capture."""
        if stats is None:
            stats = QueryStats(rank_id=self.rank_id, window_label="csv_scan", budget=max_rows)
        deadline = time.perf_counter() + max(0.1, timeout_s)
        path = Path(self.schema.path)
        with _open_csv_text(path) as handle:
            reader = csv.reader(handle)
            next(reader, None)
            for row_index, row in enumerate(reader):
                if row_index % 1024 == 0 and time.perf_counter() > deadline:
                    raise ProfilerQueryError(
                        f"{path.name}: CSV scan exceeded {timeout_s:.1f}s after {row_index} rows")
                if row_index >= max_rows:
                    raise ProfilerQueryError(
                        f"{path.name}: CSV row budget {max_rows} exceeded; narrow the capture or raise --max-rows")
                stats.rows_read += 1
                event = decode_csv_row(
                    row, row_index, self.schema, rank_id=self.rank_id,
                    rank_index=self.rank_index, stats=stats, strict=strict,
                    include_zero_duration=include_zero_duration)
                if event is not None:
                    yield event

    def read_windows(
        self,
        windows: list[Window],
        *,
        max_rows: int = 5_000_000,
        timeout_s: float = 30.0,
    ) -> dict[int, tuple[list[Event], QueryStats]]:
        started = time.perf_counter()
        results = {
            index: (list(), QueryStats(rank_id=self.rank_id, window_label=window.label or str(window.step), budget=max_rows))
            for index, window in enumerate(windows)
        }
        stats = QueryStats(rank_id=self.rank_id, window_label="csv_scan", budget=max_rows)
        for event in self.iter_events(max_rows=max_rows, timeout_s=timeout_s, stats=stats):
            for index, window in enumerate(windows):
                if event.start_ns < window.end_ns and event.end_ns > window.start_ns:
                    results[index][0].append(event)
                    window_stats = results[index][1]
                    if event.wait_status == "bound":
                        window_stats.wait_bound_rows += 1
                    if event.pmu_status == "bound":
                        window_stats.pmu_bound_rows += 1
                        window_stats.pmu_rows += len(event.pmu)
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 6)
        for index, (events, window_stats) in results.items():
            window_stats.rows_read = stats.rows_read
            window_stats.rows_selected = len(events)
            window_stats.compute_rows = len(events)
            window_stats.bad_rows = stats.bad_rows
            window_stats.elapsed_ms = elapsed_ms
            events.sort(key=lambda item: (item.start_ns, item.end_ns, item.task_id))
        return results
