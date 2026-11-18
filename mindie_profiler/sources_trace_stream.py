"""Chrome-trace event streaming: C ``ijson`` fast path with legacy replay.

[Role]
  Stream top-level Chrome trace event objects from a bare ``[`` array or a
  ``{"traceEvents": [...]}`` object root without materialising the file, and
  fall back to a fixed pure-Python incremental reader when ``ijson`` is absent
  or rejects a non-standard token.
[Invariants]
  * ``ijson`` is imported lazily inside the fast path only, so a ``--no-deps``
    wheel import and ``--help`` remain valid without it.
  * ``use_float=False`` yields ``Decimal``; ``_number``/``_ns_from_us`` accept
    it and ``json.dumps(..., default=_json_number)`` serialises numeric args.
  * ``NaN``/``Infinity`` arguments make the C backend reject the document; the
    legacy reader is replayed from the start, skipping already emitted events.
    Truncated JSON and trailing commas still raise ``ProfilerSchemaError``.
  * Every 4,096 events checks the optional caller deadline.
[Timeouts & Locks]
  Optional wall-clock deadline only; no locks, SQL or background threads.
[Side-Effect Policy]
  Reads one trace file; never writes or mutates the capture.
"""
from __future__ import annotations

import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Iterator

from .events import ProfilerQueryError, ProfilerSchemaError

_DEFAULT_CHUNK = 1024 * 1024
_DEADLINE_EVERY = 4096


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            number = Decimal(value.strip())
        except (InvalidOperation, ValueError):
            return None
        if not number.is_finite():
            return None
        return float(number)
    return None


def _ns_from_us(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
        if not number.is_finite():
            return None
        return int((number * Decimal(1000)).to_integral_value())
    except (InvalidOperation, ValueError, OverflowError):
        return None


def _json_number(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"unsupported trace argument type: {type(value).__name__}")


def _root_kind(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                return "empty"
            for char in chunk:
                if char in " \t\r\n":
                    continue
                if char == "[":
                    return "array"
                if char == "{":
                    return "object"
                return "unknown"


class _JsonStream:
    """Small incremental JSON reader; only one value is materialised at a time."""

    def __init__(self, path: Path, *, chunk_bytes: int = _DEFAULT_CHUNK) -> None:
        self.path = path
        self.chunk_bytes = max(4096, int(chunk_bytes))
        self._handle = path.open("r", encoding="utf-8")
        self._buffer = ""
        self._pos = 0
        self._eof = False
        self._decoder = json.JSONDecoder()
        self._consumed_chars = 0
        self._fill()

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "_JsonStream":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _fill(self, minimum: int | None = None) -> bool:
        if self._eof:
            return False
        size = self.chunk_bytes if minimum is None else max(self.chunk_bytes, int(minimum))
        chunk = self._handle.read(size)
        if not chunk:
            self._eof = True
            return False
        if self._pos:
            self._consumed_chars += self._pos
            self._buffer = self._buffer[self._pos:]
            self._pos = 0
        # Exponential refill bounds total buffer copying for multi-chunk values.
        self._buffer += chunk
        return True

    def _compact(self) -> None:
        if self._pos > 65536 or self._pos == len(self._buffer):
            self._consumed_chars += self._pos
            self._buffer = self._buffer[self._pos:]
            self._pos = 0

    def peek(self) -> str:
        self._skip_ws()
        return self._buffer[self._pos] if self._pos < len(self._buffer) else ""

    def _skip_ws(self) -> None:
        while True:
            size = len(self._buffer)
            while self._pos < size and self._buffer[self._pos] in " \t\r\n":
                self._pos += 1
            if self._pos < size or not self._fill():
                return

    def expect(self, char: str) -> None:
        if self.peek() != char:
            raise self._error(f"expected {char!r}")
        self._pos += 1

    def _error(self, detail: str) -> ProfilerSchemaError:
        offset = self._consumed_chars + self._pos
        return ProfilerSchemaError(f"{self.path.name}: invalid JSON trace at char {offset}: {detail}")

    def value(self) -> Any:
        self._skip_ws()
        while True:
            try:
                value, end = self._decoder.raw_decode(self._buffer, self._pos)
            except json.JSONDecodeError as exc:
                if self._fill(max(len(self._buffer), self.chunk_bytes)):
                    continue
                raise self._error(exc.msg) from exc
            if end == len(self._buffer) and not self._eof:
                if self._fill(max(len(self._buffer), self.chunk_bytes)):
                    continue
            self._pos = end
            self._compact()
            return value

    def iter_array(self) -> Iterator[Any]:
        self.expect("[")
        if self.peek() == "]":
            self._pos += 1
            self._compact()
            return
        while True:
            yield self.value()
            self._compact()
            char = self.peek()
            if char == ",":
                self._pos += 1
                continue
            if char == "]":
                self._pos += 1
                self._compact()
                return
            raise self._error("expected ',' or ']' in trace array")


def iter_trace_events_legacy(
    trace_path: str | Path, *, chunk_bytes: int = _DEFAULT_CHUNK,
    timeout_s: float | None = None,
) -> Iterator[dict[str, Any]]:
    """Pure-Python incremental reader; strict JSON errors stay explicit."""
    path = Path(trace_path)
    if not path.is_file():
        raise ProfilerSchemaError(f"trace file not found: {path}")
    deadline = None if timeout_s is None else time.perf_counter() + max(0.1, float(timeout_s))
    count = 0
    with _JsonStream(path, chunk_bytes=chunk_bytes) as stream:
        char = stream.peek()
        if char == "[":
            for item in stream.iter_array():
                count += 1
                if deadline is not None and count % _DEADLINE_EVERY == 0 and time.perf_counter() > deadline:
                    raise ProfilerQueryError(f"{path.name}: trace stream exceeded {timeout_s:.1f}s")
                if isinstance(item, dict):
                    yield item
            return
        if char != "{":
            raise stream._error("root must be an array or an object with traceEvents")
        stream.expect("{")
        found = False
        if stream.peek() == "}":
            stream._pos += 1
            raise ProfilerSchemaError(f"{path.name}: object root has no traceEvents array")
        while True:
            key = stream.value()
            stream.expect(":")
            if key == "traceEvents":
                found = True
                if stream.peek() != "[":
                    raise stream._error("traceEvents must be an array")
                for item in stream.iter_array():
                    count += 1
                    if deadline is not None and count % _DEADLINE_EVERY == 0 and time.perf_counter() > deadline:
                        raise ProfilerQueryError(f"{path.name}: trace stream exceeded {timeout_s:.1f}s")
                    if isinstance(item, dict):
                        yield item
            else:
                stream.value()
            char = stream.peek()
            if char == ",":
                self_pos = stream._pos + 1
                stream._pos = self_pos
                continue
            if char == "}":
                stream._pos += 1
                break
            raise stream._error("expected ',' or '}' in trace object")
        if not found:
            raise ProfilerSchemaError(f"{path.name}: object root has no traceEvents array")


def _fast_reader(trace_path: str | Path, root: str) -> Iterator[dict[str, Any]]:
    import ijson

    with Path(trace_path).open("rb") as handle:
        prefix = "item" if root == "array" else "traceEvents.item"
        for item in ijson.items(handle, prefix, use_float=False):
            if isinstance(item, dict):
                yield item


def _stream_with_legacy_replay(
    path: Path, fast_reader: Callable[[Path], Iterator[dict[str, Any]]],
    legacy_reader: Callable[[Path], Iterator[dict[str, Any]]],
) -> Iterator[dict[str, Any]]:
    import ijson

    emitted = 0
    try:
        for event in fast_reader(path):
            emitted += 1
            yield event
    except ijson.JSONError:
        for index, event in enumerate(legacy_reader(path)):
            if index >= emitted:
                yield event


def iter_trace_events(
    trace_path: str | Path, *, chunk_bytes: int = _DEFAULT_CHUNK,
    timeout_s: float | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield Chrome trace event objects via ``ijson``, replaying on JSON errors."""
    path = Path(trace_path)
    if not path.is_file():
        raise ProfilerSchemaError(f"trace file not found: {path}")
    root = _root_kind(path)

    def legacy(target: Path) -> Iterator[dict[str, Any]]:
        return iter_trace_events_legacy(
            target, chunk_bytes=chunk_bytes, timeout_s=timeout_s)

    def fast(target: Path) -> Iterator[dict[str, Any]]:
        deadline = None if timeout_s is None else time.perf_counter() + max(0.1, float(timeout_s))
        count = 0
        for event in _fast_reader(target, root):
            count += 1
            if deadline is not None and count % _DEADLINE_EVERY == 0 and time.perf_counter() > deadline:
                raise ProfilerQueryError(f"{target.name}: trace stream exceeded {timeout_s:.1f}s")
            yield event

    try:
        import ijson  # noqa: F401 - presence selects the fast path
    except ImportError:
        yield from legacy(path)
        return
    if root not in {"array", "object"}:
        raise ProfilerSchemaError(f"{path.name}: root must be an array or an object with traceEvents")
    if root == "object":
        # An object root with no traceEvents must stay an explicit schema error;
        # replay validates the key presence when the fast path yields nothing.
        emitted = 0
        try:
            for event in _stream_with_legacy_replay(path, fast, legacy):
                emitted += 1
                yield event
        except ProfilerSchemaError:
            raise
        if emitted == 0:
            yield from legacy(path)
        return
    yield from _stream_with_legacy_replay(path, fast, legacy)


__all__ = [
    "_JsonStream", "_json_number", "_ns_from_us", "_number", "_root_kind",
    "iter_trace_events", "iter_trace_events_legacy",
]
