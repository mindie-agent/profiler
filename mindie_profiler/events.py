"""Core records shared by the MindIE profiler pipeline.

[Role]
  Define the immutable event, explicit time-window, source-identity, and
  per-window observation records passed between source adapters, accounting,
  cross-rank statistics, and the C7 report writer.

[Invariants]
  * Internal time is integer nanoseconds.  CSV microseconds are converted
    once at the adapter boundary; reports convert to milliseconds once.
  * Each event retains its source clock domain, raw unit/tick (when the
    adapter can keep it), and any sourced scale/offset to a common reference.
    A local duration is valid inside its own domain.  Cross-domain comparison
    is allowed only through an explicitly sourced reference; it is never
    obtained from timestamp magnitude, epoch-looking values, or by
    subtracting per-rank minimum timestamps.
  * A missing measurement is ``None``, never ``0``.  Zero is only emitted
    when a real event/interval is zero length.
  * ``step`` is copied from the caller's explicit window.  No source adapter
    invents a step id from kernel order or timestamps.
  * ``wait_ns`` and ``pmu`` are measured full-capture values with explicit
    status/provenance; ambiguous task occurrences keep them empty.

[Timeouts & Locks]
  This module is pure data.  It performs no I/O and holds no locks.

[Side-Effect Policy]
  No filesystem, network, sqlite, or global-state mutation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

PARSER_VERSION = "mindie_profiler/0.5.5"
REPORT_SCHEMA = "mindie-profile-summary/1"


EVENT_IDENTITY_SCHEMA = "mindie-event-identity/1"


def composite_event_identity(
    *,
    rank_id: str,
    rank_index: int | None,
    source_kind: str,
    table: str,
    device_id: str,
    stream_id: str,
    task_id: str,
    start_ns: int,
    end_ns: int,
    locator: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a stable identity from exact occurrence fields.

    Plain ``taskId``/``globalTaskId`` is insufficient: task ids repeat in real
    captures and global task ids repeat across full-capture occurrence groups.
    The original integer interval and the source/table/rank/locator occurrence
    are part of the hash; missing fields stay ``None`` rather than being guessed.
    """
    from .repro_snapshot import snapshot
    locator = snapshot({} if locator is None else locator)
    payload = {
        "schema_version": EVENT_IDENTITY_SCHEMA,
        "rank_id": str(rank_id),
        "rank_index": rank_index,
        "source_kind": str(source_kind),
        "table": str(table),
        "device_id": str(device_id),
        "stream_id": str(stream_id),
        "task_id": str(task_id),
        "start_ns": int(start_ns),
        "end_ns": int(end_ns),
        "locator": locator,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return {"schema_version": EVENT_IDENTITY_SCHEMA, "event_id": f"event:{digest}", "payload": payload}


class ProfilerError(RuntimeError):
    """Base class for explicit, user-actionable profiler failures."""


class ProfilerSchemaError(ProfilerError):
    """The source schema is unknown or lacks required verified columns."""


class ProfilerQueryError(ProfilerError):
    """A bounded read failed, timed out, or exceeded its row budget."""


class ProfilerUsageError(ProfilerError):
    """The request cannot be honoured without inventing step/rank context."""


_REMOTE_GUIDE_HINT = (
    "If this capture resides on a remote Ascend host/container, do NOT copy raw "
    "msprof directories locally; run 'mindie-profiler remote-guide --root "
    "<remote_dir>' for in-place remote-dev commands."
)
_MISSING_PATH_TOKENS = (
    "profiling root not found", "input does not exist", "does not exist",
    "no such file", "cannot resolve input",
)


def remote_guide_hint(message: str) -> str:
    """Append the in-place remote guidance when a local path is missing."""
    text = str(message)
    if _REMOTE_GUIDE_HINT in text:
        return text
    folded = text.lower()
    if any(token in folded for token in _MISSING_PATH_TOKENS):
        return text + "\n" + _REMOTE_GUIDE_HINT
    return text


@dataclass(frozen=True, slots=True)
class ClockDomain:
    """One source clock domain and its sourced relation to a reference.

    ``scale_ns`` converts one raw source tick to integer nanoseconds; the
    adapter has already applied it to ``Event.start_ns``/``end_ns``.  The
    reference relation is optional and is applied to those local nanoseconds:

        reference_ns = round(local_ns * scale_num / scale_den) + offset_ns

    ``reference_scale_num/den`` and ``offset_ns`` are retained only when they
    come from source metadata or an explicit synchronization anchor.  The
    optional validity bounds are checked against the local timestamp; a value
    outside them is unknown, not clamped.  A domain with no sourced relation
    keeps ``reference_domain``/``offset_ns`` as ``None``; its local duration
    remains valid, but it cannot participate in cross-domain spans or ordering.
    Ratio, drift and validity are never inferred from durations or matching
    names; callers must declare them.
    """

    domain: str
    unit: str
    scale_ns: int = 1
    offset_ns: int | None = None
    reference_domain: str | None = None
    reference_scale_num: int = 1
    reference_scale_den: int = 1
    valid_from_ns: int | None = None
    valid_to_ns: int | None = None
    source: str = "unknown"

    def __post_init__(self) -> None:
        if not isinstance(self.domain, str) or not self.domain:
            raise ValueError("clock domain must be a non-empty string")
        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError("clock unit must be a non-empty string")
        if isinstance(self.scale_ns, bool) or not isinstance(self.scale_ns, int) or self.scale_ns <= 0:
            raise ValueError("clock scale_ns must be a positive integer")
        if self.reference_domain is not None:
            if not isinstance(self.reference_domain, str) or not self.reference_domain:
                raise ValueError("clock reference_domain must be a non-empty string")
            if isinstance(self.offset_ns, bool) or not isinstance(self.offset_ns, int):
                raise ValueError("a referenced clock domain requires an integer offset_ns")
        elif self.offset_ns is not None:
            raise ValueError("offset_ns is only meaningful with a reference_domain")
        for name, value in (
            ("reference_scale_num", self.reference_scale_num),
            ("reference_scale_den", self.reference_scale_den),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.reference_domain is None and (
            self.reference_scale_num != 1 or self.reference_scale_den != 1
        ):
            raise ValueError(
                "reference_scale_num/den require a reference_domain"
            )
        for name, value in (
            ("valid_from_ns", self.valid_from_ns),
            ("valid_to_ns", self.valid_to_ns),
        ):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
                raise ValueError(f"{name} must be an integer or None")
        if (
            self.valid_from_ns is not None
            and self.valid_to_ns is not None
            and self.valid_to_ns < self.valid_from_ns
        ):
            raise ValueError("valid_to_ns must not precede valid_from_ns")

    @property
    def comparable(self) -> bool:
        return self.reference_domain is not None and self.offset_ns is not None

    def to_reference_ns(self, local_ns: int) -> int | None:
        """Map local nanoseconds through the sourced relation, or ``None``.

        The optional rational ratio is applied before the constant offset and
        is rounded half away from zero at the nanosecond boundary.  Validity is
        checked against the local timestamp; an out-of-range value is unknown,
        not clamped.
        """
        if not self.comparable:
            return None
        local_ns = int(local_ns)
        if self.valid_from_ns is not None and local_ns < self.valid_from_ns:
            return None
        if self.valid_to_ns is not None and local_ns > self.valid_to_ns:
            return None
        numerator = local_ns * int(self.reference_scale_num)
        denominator = int(self.reference_scale_den)
        sign = -1 if numerator < 0 else 1
        quotient, remainder = divmod(abs(numerator), denominator)
        if remainder * 2 >= denominator:
            quotient += 1
        return sign * quotient + int(self.offset_ns)

    def shares_reference_with(self, other: "ClockDomain") -> bool:
        return (
            self.comparable
            and other.comparable
            and self.reference_domain == other.reference_domain
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "unit": self.unit,
            "scale_ns": self.scale_ns,
            "offset_ns": self.offset_ns,
            "reference_domain": self.reference_domain,
            "reference_scale_num": self.reference_scale_num,
            "reference_scale_den": self.reference_scale_den,
            "valid_from_ns": self.valid_from_ns,
            "valid_to_ns": self.valid_to_ns,
            "source": self.source,
        }


UNKNOWN_CLOCK = ClockDomain(
    domain="unknown",
    unit="unknown",
    source="source did not declare a clock domain; no cross-domain relation is available",
)

_CSV_US_CLOCK = ClockDomain(
    domain="kernel_details_csv_us",
    unit="us",
    scale_ns=1000,
    offset_ns=None,
    reference_domain=None,
    source=(
        "kernel_details.csv Start Time(us) is microseconds and was converted "
        "once to integer ns at the adapter boundary; the adapter supplies no "
        "cross-rank synchronization anchor; raw microsecond tick is not retained"
    ),
)


@dataclass(frozen=True, slots=True)
class Window:
    """One explicitly supplied analysis window (all times are ns)."""

    start_ns: int
    end_ns: int
    step: int | None = None
    label: str | None = None
    source: str = "explicit"
    clock: ClockDomain | None = None

    def __post_init__(self) -> None:
        if self.end_ns <= self.start_ns:
            raise ProfilerUsageError(
                f"window {self.label or self.step!r} must have end_ns > start_ns "
                f"(got {self.start_ns}..{self.end_ns})"
            )

    @property
    def span_ns(self) -> int:
        return self.end_ns - self.start_ns


@dataclass(slots=True)
class Event:
    """One device event reconstructed from the DB or kernel_details.csv."""

    rank_id: str
    rank_index: int | None
    name: str
    op_type: str
    task_type: str
    core: str
    stream_id: str
    task_id: str
    device_id: str
    start_ns: int
    end_ns: int
    source_kind: str
    table: str
    clock: ClockDomain = UNKNOWN_CLOCK
    clock_start_tick: int | str | None = None
    clock_duration_tick: int | str | None = None
    clock_end_tick: int | str | None = None
    source_id: str | None = None
    capture_id: str | None = None
    table_kind: str | None = None
    field_presence: dict[str, bool] = field(default_factory=dict)
    block: str = "Unclassified"
    mapping_rule: str = "residual_unmapped"
    execution_engine: str = "unknown"
    # Deprecated: never derive this from ``execution_engine`` alone.  It stays
    # ``unknown`` unless a measured PMU/wait/AICPU evidence fragment is bound.
    bound_family: str = "unknown"
    is_comm: bool = False
    is_aicpu: bool = False
    input_shapes: str = ""
    input_dtypes: str = ""
    input_formats: str = ""
    output_shapes: str = ""
    output_dtypes: str = ""
    output_formats: str = ""
    block_dim: int | None = None
    mix_block_dim: int | None = None
    op_state: str = ""
    wait_ns: int | None = None
    wait_status: str = "not_available"
    wait_source: str | None = None
    wait_provenance: dict[str, Any] = field(default_factory=dict)
    pmu: tuple[tuple[str, float], ...] = ()
    pmu_status: str = "not_available"
    pmu_source: str | None = None
    pmu_kind: str = "unknown"
    pmu_provenance: dict[str, Any] = field(default_factory=dict)
    task_occurrences_full_capture: int | None = None
    locator: dict[str, Any] = field(default_factory=dict)

    def identity(self) -> dict[str, Any]:
        return composite_event_identity(
            rank_id=self.rank_id,
            rank_index=self.rank_index,
            source_kind=self.source_kind,
            table=self.table,
            device_id=self.device_id,
            stream_id=self.stream_id,
            task_id=self.task_id,
            start_ns=self.start_ns,
            end_ns=self.end_ns,
            locator=self.locator,
        )

    @property
    def event_id(self) -> str:
        return str(self.identity()["event_id"])

    @property
    def duration_ns(self) -> int:
        return max(0, self.end_ns - self.start_ns)

    def __post_init__(self) -> None:
        # CSV adapters convert microseconds to nanoseconds before creating
        # this record; the adapter supplies the raw tick fields where the
        # layout has them.  Declared units/scale are retained, epoch magnitude
        # never establishes a shared reference, and no offset is fitted.
        if isinstance(self.locator, Mapping):
            from .repro_values import bounded_mapping
            self.locator = bounded_mapping(self.locator, "event locator")
        if self.source_kind == "kernel_details_csv" and self.clock == UNKNOWN_CLOCK:
            self.clock = _CSV_US_CLOCK

    @property
    def clock_comparable(self) -> bool:
        return self.clock.comparable

    def reference_interval_ns(self) -> tuple[int, int] | None:
        """Return the interval in its declared reference domain, when sourced."""
        start_ns = self.clock.to_reference_ns(self.start_ns)
        end_ns = self.clock.to_reference_ns(self.end_ns)
        if start_ns is None or end_ns is None:
            return None
        return start_ns, end_ns

    def clipped(self, start_ns: int, end_ns: int) -> tuple[int, int] | None:
        left = max(self.start_ns, start_ns)
        right = min(self.end_ns, end_ns)
        if right <= left:
            return None
        return left, right

    def complete_in(self, start_ns: int, end_ns: int) -> bool:
        return self.start_ns >= start_ns and self.end_ns <= end_ns

    def pmu_map(self) -> dict[str, float]:
        return dict(self.pmu)


@dataclass(frozen=True, slots=True)
class SourceRef:
    """Identity of one rank's chosen kernel event source."""

    rank_id: str
    rank_index: int | None
    kind: str
    path: str
    basename: str
    sha256: str | None
    size_bytes: int
    schema_version: str
    schema_variant: str
    header_sha256: str | None = None
    optional_missing: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    mtime_ns: int | None = None

    def content_identity(self) -> dict[str, Any]:
        """Cheap cache identity used unless an explicit ``--hash`` is requested."""

        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "mtime_ns": self.mtime_ns,
            "schema_version": self.schema_version,
            "sha256": self.sha256,
        }


@dataclass(slots=True)
class QueryStats:
    """Measured cost and coverage of one bounded source read."""

    rank_id: str
    window_label: str
    rows_read: int = 0
    rows_selected: int = 0
    compute_rows: int = 0
    comm_rows: int = 0
    comm_sched_rows: int = 0
    bad_rows: int = 0
    unresolved_string_ids: int = 0
    pmu_rows: int = 0
    pmu_bad_values: int = 0
    wait_bound_rows: int = 0
    wait_ambiguous_rows: int = 0
    pmu_bound_rows: int = 0
    pmu_ambiguous_rows: int = 0
    ambiguous_groups: int = 0
    measurement_scan_ms: float = 0.0
    elapsed_ms: float = 0.0
    budget: int | None = None

    def merge(self, other: "QueryStats") -> None:
        self.rows_read += other.rows_read
        self.rows_selected += other.rows_selected
        self.compute_rows += other.compute_rows
        self.comm_rows += other.comm_rows
        self.comm_sched_rows += other.comm_sched_rows
        self.bad_rows += other.bad_rows
        self.unresolved_string_ids += other.unresolved_string_ids
        self.pmu_rows += other.pmu_rows
        self.pmu_bad_values += other.pmu_bad_values
        self.wait_bound_rows += other.wait_bound_rows
        self.wait_ambiguous_rows += other.wait_ambiguous_rows
        self.pmu_bound_rows += other.pmu_bound_rows
        self.pmu_ambiguous_rows += other.pmu_ambiguous_rows
        self.ambiguous_groups += other.ambiguous_groups
        self.measurement_scan_ms = round(self.measurement_scan_ms + other.measurement_scan_ms, 6)
        self.elapsed_ms = round(self.elapsed_ms + other.elapsed_ms, 6)


@dataclass(slots=True)
class Observation:
    """Accounting for one rank inside one explicit window."""

    rank_id: str
    rank_index: int | None
    window: Window
    accounting: Any
    events: list[Event]
    source: SourceRef
    stats: QueryStats

    def identity(self) -> dict[str, Any]:
        payload = {
            "rank_id": self.rank_id,
            "rank_index": self.rank_index,
            "source_kind": self.source.kind,
            "source_sha256": self.source.sha256,
            "window_start_ns": self.window.start_ns,
            "window_end_ns": self.window.end_ns,
            "step": self.window.step,
            "label": self.window.label,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
        return {"observation_id": f"observation:{digest}", "payload": payload}
