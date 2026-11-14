"""Compact row projection for one open decode forward segment.

[Role]
  Project a streamed source ``Event`` into the minimal closure fields read by
  decode forward alignment without retaining full source event payloads.

[Invariants]
  * ``_FieldShare`` interns only low-cardinality strings and parsed shape tuples
    within one open ``(rank_id, device_id)`` window (bounded by
    ``_MAX_POOL_ENTRIES``).
  * High-cardinality strings (task ids, row numbers, malformed shape strings)
    stay on the active row and are never inserted into shared pools.
  * Closing a rank window drops that rank's pool without touching other ranks.

[Timeouts & Locks]
  Pure in-memory projection; no I/O, timers, or locks.

[Side-Effect Policy]
  Does not mutate source ``Event`` instances or external state.
"""

from __future__ import annotations

from dataclasses import dataclass

from .normalized import shapes

_LOCATOR_SHARED_KEYS = {"source", "table", "stream_id", "device_id"}
_MAX_POOL_ENTRIES = 8_192


class _FieldShare:
    """Intern repeated low-cardinality values for one open rank window."""

    __slots__ = ("strings", "shapes")

    def __init__(self) -> None:
        self.strings: dict[str, str] = {}
        self.shapes: dict[tuple, tuple] = {}

    def text(self, value: object) -> object:
        if not isinstance(value, str):
            return value
        found = self.strings.get(value)
        if found is not None:
            return found
        if len(self.strings) < _MAX_POOL_ENTRIES:
            self.strings[value] = value
        return value

    def shape(self, parsed: tuple) -> tuple:
        found = self.shapes.get(parsed)
        if found is not None:
            return found
        if len(self.shapes) < _MAX_POOL_ENTRIES:
            self.shapes[parsed] = parsed
        return parsed


def _parsed_shape(text: str, share: _FieldShare) -> tuple[tuple | None, str | None]:
    """Keep a parsed shape; blank descriptors store neither text nor a tuple."""
    stripped = text.strip().strip('"')
    if stripped in {"", "N/A", "NULL"}:
        return None, None
    parsed = shapes(text)
    if parsed is None:
        if stripped in {"NA", "None"}:
            return None, None
        return None, text
    return share.shape(parsed), None


def _shape_text(parsed: tuple | None, raw: str | None) -> str:
    if raw is not None:
        return raw
    if parsed is None:
        return "N/A"
    return ";".join(",".join(str(dim) for dim in shape) for shape in parsed)


def _locator_items(locator: dict, share: _FieldShare) -> tuple:
    items = []
    for key, value in locator.items():
        items.append(share.text(key) if isinstance(key, str) else key)
        if isinstance(value, str) and key in _LOCATOR_SHARED_KEYS:
            value = share.text(value)
        items.append(value)
    return tuple(items)


@dataclass(slots=True)
class _ActiveEvent:
    """One open-segment row: closure fields only, not the full source Event."""

    op_type: str
    name: str
    core: str
    task_type: str
    stream_id: str
    task_id: str
    device_id: str
    rank_id: str
    op_state: str
    start_ns: int
    end_ns: int
    block_dim: object
    mix_block_dim: object
    has_pmu: bool
    inputs: object
    outputs: object
    input_shape_raw: object
    output_shape_raw: object
    input_dtypes: str
    output_dtypes: str
    input_formats: str
    output_formats: str
    locator_items: tuple

    @property
    def event(self) -> _ActiveEvent:
        return self

    @property
    def kind(self) -> str:
        return self.op_type

    @property
    def duration_ns(self) -> int:
        return max(0, self.end_ns - self.start_ns)

    @property
    def pmu(self) -> tuple:
        return (("", 0.0),) if self.has_pmu else ()

    @property
    def input_shapes(self) -> str:
        return _shape_text(self.inputs, self.input_shape_raw)

    @property
    def output_shapes(self) -> str:
        return _shape_text(self.outputs, self.output_shape_raw)

    @property
    def locator(self) -> dict:
        items = self.locator_items
        return {items[index]: items[index + 1] for index in range(0, len(items), 2)}


def _active_event(event: object, share: _FieldShare) -> _ActiveEvent:
    """Project one streamed event into the active per-rank row."""
    inputs, input_raw = _parsed_shape(event.input_shapes, share)
    outputs, output_raw = _parsed_shape(event.output_shapes, share)
    return _ActiveEvent(
        op_type=share.text(event.op_type),
        name=share.text(event.name),
        core=share.text(event.core),
        task_type=share.text(event.task_type),
        stream_id=share.text(event.stream_id),
        task_id=event.task_id,
        device_id=share.text(event.device_id),
        rank_id=share.text(event.rank_id),
        op_state=share.text(event.op_state),
        start_ns=event.start_ns,
        end_ns=event.end_ns,
        block_dim=event.block_dim,
        mix_block_dim=event.mix_block_dim,
        has_pmu=bool(event.pmu),
        inputs=inputs,
        outputs=outputs,
        input_shape_raw=input_raw,
        output_shape_raw=output_raw,
        input_dtypes=share.text(event.input_dtypes),
        output_dtypes=share.text(event.output_dtypes),
        input_formats=share.text(event.input_formats),
        output_formats=share.text(event.output_formats),
        locator_items=_locator_items(event.locator, share),
    )


def note_pool(probe: dict[str, int], pools: dict, active: dict) -> None:
    """Record live and high-water sizes of pools still owned by open ranks."""
    strings = sum(len(pool.strings) for pool in pools.values())
    shape_count = sum(len(pool.shapes) for pool in pools.values())
    rows = sum(len(chunk) for chunk in active.values())
    probe["live_strings"] = strings
    probe["live_shapes"] = shape_count
    probe["live_active"] = rows
    if strings > probe["high_strings"]:
        probe["high_strings"] = strings
    if shape_count > probe["high_shapes"]:
        probe["high_shapes"] = shape_count
    if rows > probe["high_active"]:
        probe["high_active"] = rows


__all__ = ["_ActiveEvent", "_FieldShare", "_active_event", "note_pool"]
