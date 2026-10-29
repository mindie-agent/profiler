"""Complete tensor and occurrence views over normalized profiler events.

[Role] Expose one streaming CSV reader and a projection of existing DB/CSV events.
[Invariants] Raw tensor descriptors and integer nanoseconds retain their source;
  unknown tensors stay unknown. A kernel row never implies a model layer.
[Timeouts & Locks] CsvSource owns bounded scans; event projection is in memory.
[Side-Effect Policy] Read-only; no imports of device runtimes or simulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .events import Event
from .sources_csv import CsvSource, probe_csv
from .sources_db import load_mapping


def shapes(text: str) -> tuple[tuple[int, ...], ...] | None:
    """Parse every tensor, preserving empty optional/scalar descriptors."""
    text = text.strip().strip('"')
    if text in {"", "N/A", "NULL"}:
        return None
    try:
        return tuple(tuple(int(value) for value in shape.split(",")) if shape else ()
                     for shape in text.split(";"))
    except ValueError:
        return None


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in text.strip().strip('"').split(";")) if text else ()


@dataclass(frozen=True)
class KernelRow:
    source: str
    line: int | None
    name: str
    kind: str
    core: str
    state: str
    stream: str
    start_ns: int
    duration_ns: int
    blocks: int | None
    input_shapes: tuple | None
    output_shapes: tuple | None
    input_dtypes: tuple[str, ...]
    output_dtypes: tuple[str, ...]
    input_formats: tuple[str, ...]
    output_formats: tuple[str, ...]
    counters_us: dict[str, float]
    event: Event

    @property
    def end_ns(self) -> int:
        return self.start_ns + self.duration_ns

    @property
    def signature(self) -> tuple:
        return (self.name, self.core, self.state, self.blocks, self.input_shapes,
                self.output_shapes, self.input_dtypes, self.output_dtypes,
                self.input_formats, self.output_formats)

    @property
    def event_id(self) -> str:
        return self.event.event_id

    @property
    def identity(self) -> dict:
        return self.event.identity()


def row_from_event(event: Event, *, source: str | Path | None = None) -> KernelRow:
    """Project an analysis Event without re-reading its source or changing identity."""
    counters = {}
    metrics = load_mapping()["pmu_metrics"]
    for key, value in event.pmu:
        spec = metrics.get(key, {})
        column = spec.get("csv_column", "")
        if spec.get("unit") == "ns" and column.endswith("_time(us)"):
            counters[column] = value / 1000
    return KernelRow(
        source=str(source if source is not None else event.locator.get("source", "")),
        line=event.locator.get("csv_line"),
        name=event.name, kind=event.op_type, core=event.core, state=event.op_state,
        stream=event.stream_id, start_ns=event.start_ns, duration_ns=event.duration_ns,
        blocks=event.block_dim, input_shapes=shapes(event.input_shapes),
        output_shapes=shapes(event.output_shapes), input_dtypes=_tokens(event.input_dtypes),
        output_dtypes=_tokens(event.output_dtypes), input_formats=_tokens(event.input_formats),
        output_formats=_tokens(event.output_formats), counters_us=counters, event=event,
    )


def kernel_rows(path: str | Path, *, rank_id: str = "", rank_index: int | None = None,
                max_rows: int = 5_000_000, timeout_s: float = 30.0,
                include_zero_duration: bool = False):
    """Stream the shared decoder; marker consumers may retain zero-duration rows."""
    source = CsvSource(probe_csv(path), rank_id=rank_id, rank_index=rank_index)
    for event in source.iter_events(max_rows=max_rows, timeout_s=timeout_s, strict=True,
                                    include_zero_duration=include_zero_duration):
        yield row_from_event(event)
