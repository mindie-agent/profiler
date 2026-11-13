"""BIND1 native-call signature matching, raw HCCL alias deduplication, and graph seal check.

[Role]
  Resolve declared ``mindie-sim`` native-call bindings (``BIND1``) and signed
  rank-local HCCL raw task aliases during ``StructureMapper`` window scans
  without conflating name/shape correspondence with occurrence proof.

[Invariants]
  * ``_verify_graph_id`` accepts both the current ``mindie-sim`` seal (which
    excludes derived ``native_calls`` and ``native_call_coverage`` alongside
    ``graph_id``/``source``) and the historical seal.
  * Declared native-call entry/kernel names correspond only when the captured
    tensor signature agrees with ``typed``; ``occurrence_binding_implied`` and
    ``observed_proof`` remain ``False`` for signature-only correspondence.
  * Raw relational identity (``rank_id``, ``global_task_id``, ``stream_id``,
    ``task_id``, ``connection_id``, ``device_id``, ``start_ns``, ``end_ns``) is
    tracked across all examined window events (never truncated by
    ``mapping_limit``) and deduplicated via true interval union.

[Timeouts & Locks]
  Pure in-memory per-window tracking bounded by ``max_events``; no I/O or locks.

[Side-Effect Policy]
  Mutates only the mapper-owned cache and retained sample rows for the active
  mapping pass; no external side effects.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from typing import Any, Callable, Mapping

from .accounting import merge_intervals
from .events import Event, ProfilerUsageError

_DTYPE_TOKENS = {
    "DT_BF16": "bf16",
    "DT_BFLOAT16": "bf16",
    "DT_FLOAT16": "fp16",
    "DT_FLOAT": "fp32",
    "DT_INT8": "int8",
    "DT_INT32": "int32",
    "DT_INT64": "int64",
    "DT_UINT8": "uint8",
    "DT_UINT32": "uint32",
    "DT_BOOL": "bool",
    "DT_DOUBLE": "fp64",
    "DT_FLOAT8_E4M3FN": "fp8_e4m3",
    "DT_FLOAT8_E5M2": "fp8_e5m2",
    "DT_FLOAT8_E8M0": "fp8_e8m0",
}


def _freeze(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze(item)) for key, item in value.items()))
    return value


def _union_ns(intervals: list[tuple[int, int]]) -> int:
    return sum(right - left for left, right in merge_intervals(intervals))


def _seal_digest(payload: Mapping[str, Any]) -> str:
    digest = sha256()
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    for chunk in encoder.iterencode(payload):
        digest.update(chunk.encode("utf-8"))
    return "sha256:" + digest.hexdigest()


def verify_graph_id(structure: Mapping[str, Any]) -> str:
    declared = structure.get("graph_id")
    current = _seal_digest(
        {
            key: value
            for key, value in structure.items()
            if key not in {"graph_id", "source", "native_calls", "native_call_coverage"}
        }
    )
    if declared == current:
        return current
    legacy = _seal_digest(
        {key: value for key, value in structure.items() if key not in {"graph_id", "source"}}
    )
    if declared == legacy:
        return legacy
    raise ProfilerUsageError(
        "structure graph_id does not match its contents; re-export the structure"
    )


_NON_CONTIGUOUS_FORMATS = frozenset({"FRACTAL_NZ", "FRACTAL_Z", "NC1HWC0", "C1HWNCoC0"})


def _norm_dtype(raw: Any) -> str | None:
    text = str(raw or "").strip().strip('"')
    if not text or text in {"N/A", "NULL", "None"}:
        return None
    return _DTYPE_TOKENS.get(text.upper(), text.lower().removeprefix("dt_"))


def _parse_shape_lanes(text: str | None) -> tuple[tuple[int, ...], ...] | None:
    rows: list[tuple[int, ...]] = []
    for part in (text or "").split(";"):
        cell = part.strip().strip('"')
        if not cell or cell in {"N/A", "NULL", "None"}:
            continue
        try:
            dims = tuple(int(value) for value in cell.split(",") if value.strip())
        except ValueError:
            return None
        if dims:
            rows.append(dims)
    return tuple(rows)


def _parse_dtype_lanes(text: str | None) -> tuple[str, ...]:
    rows: list[str] = []
    for part in (text or "").split(";"):
        dt = _norm_dtype(part)
        if dt is not None:
            rows.append(dt)
    return tuple(rows)


def _parse_format_lanes(text: str | None) -> tuple[str, ...]:
    rows: list[str] = []
    for part in (text or "").split(";"):
        cell = part.strip().strip('"').upper()
        if cell and cell not in {"N/A", "NULL", "NONE"}:
            rows.append(cell)
    return tuple(rows)


def event_signature(
    event: Event,
) -> tuple[tuple[tuple[int, ...], ...], tuple[str, ...]] | None:
    """Parsed shape/dtype lanes of a captured event, or None when incomplete."""
    inputs = _parse_shape_lanes(event.input_shapes)
    outputs = _parse_shape_lanes(event.output_shapes)
    input_dtypes = _parse_dtype_lanes(event.input_dtypes)
    output_dtypes = _parse_dtype_lanes(event.output_dtypes)
    if inputs is None or outputs is None or not inputs or not outputs:
        return None
    if not input_dtypes or not output_dtypes:
        return None
    if len(inputs) != len(input_dtypes) or len(outputs) != len(output_dtypes):
        return None
    return (*inputs, *outputs), (*input_dtypes, *output_dtypes)


def event_raw_identity(event: Event) -> tuple[str, ...] | None:
    """Signed raw task identity used for one HCCL call's rank-local aliases."""
    locator = event.locator or {}
    global_task = locator.get(
        "global_task_id", locator.get("globalTaskId", locator.get("task_global_id"))
    )
    connection = locator.get("connection_id", locator.get("connectionId"))
    if global_task in (None, "") or connection in (None, ""):
        return None
    if event.stream_id == "" or event.task_id == "":
        return None
    return (
        str(event.rank_id),
        str(global_task),
        str(event.stream_id),
        str(event.task_id),
        str(connection),
        str(event.device_id),
        str(event.start_ns),
        str(event.end_ns),
    )


_COARSE_SHAPE_KEYS = frozenset({"local", "padded", "launch", "payload"})
_OUTPUT_SHAPE_KEYS = frozenset({"output", "out", "y", "outputs"})
_PRIMARY_INPUT_KEYS = ("input", "x", "query", "q")
_OPTIONAL_INPUT_KEYS = frozenset(
    {
        "bias",
        "scale",
        "input_scale",
        "weight_scale",
        "group_list",
        "indices",
        "sparse_indices",
        "residual",
    }
)


def _counter_leq(left: Counter[tuple[int, ...]], right: Counter[tuple[int, ...]]) -> bool:
    return all(left[key] <= right[key] for key in left)


def _as_shape_tuple(value: Any) -> tuple[int, ...] | None:
    if (
        isinstance(value, (list, tuple))
        and value
        and all(isinstance(v, int) and not isinstance(v, bool) for v in value)
    ):
        return tuple(value)
    return None


def _match_declared_shapes(
    shapes_field: Any,
    in_shapes: tuple[tuple[int, ...], ...],
    out_shapes: tuple[tuple[int, ...], ...],
) -> bool | None:
    if not isinstance(shapes_field, Mapping) or not shapes_field:
        return False
    coarse_shapes: dict[str, tuple[int, ...]] = {}
    input_roles: dict[str, tuple[int, ...]] = {}
    output_roles: dict[str, tuple[int, ...]] = {}
    explicit_inputs: tuple[tuple[int, ...], ...] | None = None
    explicit_outputs: tuple[tuple[int, ...], ...] | None = None

    for raw_key, raw_val in shapes_field.items():
        key = str(raw_key).strip().lower()
        if key in {"inputs", "outputs"} and isinstance(raw_val, (list, tuple)):
            parsed_seq = [_as_shape_tuple(item) for item in raw_val]
            if parsed_seq and all(item is not None for item in parsed_seq):
                seq = tuple(item for item in parsed_seq if item is not None)
                if key == "inputs":
                    explicit_inputs = seq
                else:
                    explicit_outputs = seq
                continue
        shape = _as_shape_tuple(raw_val)
        if shape is None:
            continue
        if key in _COARSE_SHAPE_KEYS:
            coarse_shapes[key] = shape
        elif key in _OUTPUT_SHAPE_KEYS:
            output_roles[key] = shape
        else:
            input_roles[key] = shape

    has_explicit_roles = bool(
        input_roles or output_roles or explicit_inputs is not None or explicit_outputs is not None
    )
    if not has_explicit_roles:
        if not coarse_shapes:
            return False
        coarse_set = set(coarse_shapes.values())
        if any(s not in coarse_set for s in (*in_shapes, *out_shapes)):
            return False
        if len(in_shapes) == 1 and len(out_shapes) == 1 and in_shapes[0] == out_shapes[0]:
            return True
        return None

    if explicit_outputs is not None:
        if out_shapes != explicit_outputs:
            return False
    elif output_roles:
        if Counter(out_shapes) != Counter(output_roles.values()):
            return False
    elif out_shapes:
        coarse_set = set(coarse_shapes.values())
        if not coarse_set:
            return None
        if any(s not in coarse_set for s in out_shapes):
            return False
        if len(out_shapes) > 1:
            return None

    if explicit_inputs is not None:
        if in_shapes != explicit_inputs:
            return False
    elif input_roles:
        for pkey in _PRIMARY_INPUT_KEYS:
            if pkey in input_roles and in_shapes:
                if in_shapes[0] != input_roles[pkey]:
                    return False
                break
        req_counts = Counter(
            shape for k, shape in input_roles.items() if k not in _OPTIONAL_INPUT_KEYS
        )
        all_counts = Counter(input_roles.values())
        obs_counts = Counter(in_shapes)
        if not (_counter_leq(req_counts, obs_counts) and _counter_leq(obs_counts, all_counts)):
            return False
    elif in_shapes:
        coarse_set = set(coarse_shapes.values())
        if not coarse_set:
            return None
        if any(s not in coarse_set for s in in_shapes):
            return False
        if len(in_shapes) > 1:
            return None
    return True


def native_call_signature_match(binding: Mapping[str, Any], event: Event) -> bool | None:
    """True/False across role-matched input/output shapes, dtypes, and formats; None if unresolved."""
    in_shapes = _parse_shape_lanes(event.input_shapes)
    out_shapes = _parse_shape_lanes(event.output_shapes)
    in_dtypes = _parse_dtype_lanes(event.input_dtypes)
    out_dtypes = _parse_dtype_lanes(event.output_dtypes)
    if in_shapes is None or out_shapes is None or not in_shapes or not out_shapes:
        return None
    if not in_dtypes or not out_dtypes:
        return None
    if len(in_shapes) != len(in_dtypes) or len(out_shapes) != len(out_dtypes):
        return False

    typed = binding.get("typed") or {}
    attrs = typed.get("attrs") if isinstance(typed.get("attrs"), Mapping) else {}
    shape_verdict = _match_declared_shapes(typed.get("shapes"), in_shapes, out_shapes)
    if shape_verdict is not True:
        return shape_verdict

    declared_dtype = _norm_dtype(typed.get("dtype"))
    declared_out_dtype = _norm_dtype(typed.get("output_dtype") or attrs.get("output_dtype"))
    explicit_in_dtypes = typed.get("input_dtypes")
    if isinstance(explicit_in_dtypes, (list, tuple)):
        expected_in = tuple(dt for raw in explicit_in_dtypes if (dt := _norm_dtype(raw)) is not None)
        if in_dtypes != expected_in:
            return False
    elif declared_dtype is not None:
        allowed_in = {declared_dtype}
        for key in (
            "weight_dtype",
            "cache_dtype",
            "group_list_dtype",
            "index_dtype",
            "scale_dtype",
            "input_scale_dtype",
        ):
            if (aux := _norm_dtype(typed.get(key) or attrs.get(key))) is not None:
                allowed_in.add(aux)
        if in_dtypes[0] != declared_dtype or any(dt not in allowed_in for dt in in_dtypes):
            return False

    explicit_out_dtypes = typed.get("output_dtypes")
    if isinstance(explicit_out_dtypes, (list, tuple)):
        expected_out = tuple(
            dt for raw in explicit_out_dtypes if (dt := _norm_dtype(raw)) is not None
        )
        if out_dtypes != expected_out:
            return False
    else:
        target_out = declared_out_dtype or declared_dtype
        if target_out is not None:
            allowed_out = {target_out}
            if declared_dtype is not None:
                allowed_out.add(declared_dtype)
            if out_dtypes[0] != target_out or any(dt not in allowed_out for dt in out_dtypes):
                return False

    in_formats = _parse_format_lanes(event.input_formats)
    out_formats = _parse_format_lanes(event.output_formats)
    if isinstance(typed.get("input_formats"), (list, tuple)):
        if not in_formats:
            return None
        expected_in_fmt = tuple(str(x).strip().upper() for x in typed["input_formats"])
        if in_formats != expected_in_fmt:
            return False
    if isinstance(typed.get("output_formats"), (list, tuple)):
        if not out_formats:
            return None
        expected_out_fmt = tuple(str(x).strip().upper() for x in typed["output_formats"])
        if out_formats != expected_out_fmt:
            return False
    layout = str(typed.get("layout") or "").strip().lower()
    if layout:
        if not in_formats or not out_formats:
            return None
        if layout in {"contiguous", "nd"}:
            if any(fmt in _NON_CONTIGUOUS_FORMATS for fmt in (*in_formats, *out_formats)):
                return False
        elif "fractal_nz" in layout and "FRACTAL_NZ" not in in_formats:
            return False
    return True


_MAX_IMPLEMENTATION_CACHE = 4096


def resolve_implementation_correspondence(
    cache: dict[tuple[Any, ...], dict[str, Any] | None],
    target_index: Any,
    rank_candidates_fn: Callable[[Any, str], list[str]],
    kind: str,
    rank: str,
    event: Event | None = None,
) -> dict[str, Any] | None:
    signature = event_signature(event) if event is not None else None
    raw = event_raw_identity(event) if event is not None else None
    matched_raw = raw if (raw is not None and raw in target_index.native_call_observed) else None
    alt_name = event.name if (event is not None and event.name and event.name != kind) else None
    event_match_key = (
        None
        if event is None
        else (
            _parse_shape_lanes(event.input_shapes),
            _parse_shape_lanes(event.output_shapes),
            _parse_dtype_lanes(event.input_dtypes),
            _parse_dtype_lanes(event.output_dtypes),
            _parse_format_lanes(event.input_formats),
            _parse_format_lanes(event.output_formats),
        )
    )
    cache_key = (
        kind,
        alt_name,
        rank,
        event_match_key,
        matched_raw,
    )
    if cache_key in cache:
        return cache[cache_key]

    targets: list[str] = []
    basis = "declared_native_implementation"
    signature_match: bool | None = None
    matched_label = kind

    if matched_raw is not None:
        alias_targets = list(
            dict.fromkeys(
                rank_candidates_fn(target_index.native_call_observed.get(matched_raw, ()), rank)
            )
        )
        alias_bindings = [
            target_index.native_bindings[key]
            for key in alias_targets
            if key in target_index.native_bindings
        ]
        alias_call_ids = {row.get("call_id") for row in alias_bindings if row.get("call_id")}
        alias_owners = {
            (
                str(target_index.all.get(key, {}).get("replica")),
                str(target_index.all.get(key, {}).get("stage")),
                (target_index.native_bindings[key].get("timing_owner") or {}).get("op_id")
                or target_index.native_bindings[key].get("op_id")
                or key,
            )
            for key in alias_targets
            if key in target_index.native_bindings
        }
        if (
            alias_targets
            and len(alias_bindings) == len(alias_targets)
            and len(alias_call_ids) == 1
            and len(alias_owners) == 1
        ):
            targets = alias_targets
            basis = "observed_hccl_alias_same_call"
            signature_match = True

    if not targets:
        impl_targets = list(
            dict.fromkeys(
                rank_candidates_fn(target_index.native_implementations.get(kind, ()), rank)
            )
        )
        if impl_targets:
            targets = impl_targets
            if event is not None:
                bound = [
                    target_index.native_bindings[node]
                    for node in targets
                    if node in target_index.native_bindings
                ]
                if bound:
                    verdicts = {native_call_signature_match(item, event) for item in bound}
                    if verdicts == {True}:
                        signature_match = True
                    elif False in verdicts:
                        signature_match = False

    if not targets:
        names = (kind,) if alt_name is None else (kind, alt_name)
        for candidate_name in names:
            raw_candidates = list(
                dict.fromkeys(
                    [
                        *target_index.native_call_entries.get(candidate_name, ()),
                        *target_index.native_call_kernels.get(candidate_name, ()),
                    ]
                )
            )
            candidates = rank_candidates_fn(raw_candidates, rank)
            if not candidates:
                continue
            if event is not None:
                matched = [
                    node
                    for node in candidates
                    if native_call_signature_match(target_index.native_bindings[node], event)
                    is True
                ]
                if matched:
                    targets = matched
                    signature_match = True
                    matched_label = candidate_name
                    basis = "declared_native_call_signature"
                    break
            else:
                targets = candidates
                matched_label = candidate_name
                basis = "declared_native_call_no_event"
                break

    if targets:
        description = target_index.describe_implementation(matched_label, targets)
        if (
            event is not None
            and basis == "declared_native_implementation"
            and signature_match is not True
        ):
            description["native_call"] = None
        observed_alias = (
            basis == "observed_hccl_alias_same_call"
            and description.get("native_call") is not None
            and bool((description["native_call"].get("timing_owner") or {}).get("op_id"))
        )
        description.update(
            basis=basis,
            rank=rank,
            observed_signature=(
                {
                    "shapes": [list(shape) for shape in signature[0]],
                    "dtypes": list(signature[1]),
                }
                if signature is not None
                else None
            ),
            raw_identity=(
                {
                    "rank_id": matched_raw[0],
                    "global_task_id": matched_raw[1],
                    "stream_id": matched_raw[2],
                    "task_id": matched_raw[3],
                    "connection_id": matched_raw[4],
                    "device_id": matched_raw[5],
                    "start_ns": matched_raw[6],
                    "end_ns": matched_raw[7],
                }
                if observed_alias and matched_raw is not None
                else None
            ),
            signature_match=signature_match,
            observed_proof=observed_alias,
            prepare_only_control=not observed_alias,
            occurrence_binding_implied=observed_alias,
        )
        call = description.get("native_call") or {}
        if call.get("call_id"):
            description["call_ids"] = [call["call_id"]]
    else:
        description = None

    if len(cache) >= _MAX_IMPLEMENTATION_CACHE:
        cache.clear()
    cache[cache_key] = description
    return description


_MAX_ACTIVE_RAW_CARRYOVER = 4096


class NativeCallGlobalTracker:
    """Bounded cross-window tracker retaining only unclosed spanning raw identities."""

    def __init__(self) -> None:
        self.primary_by_raw: dict[tuple[str, ...], str] = {}
        self.presentation_counts: Counter[tuple[str, ...]] = Counter()
        self.identity_counts: Counter[str] = Counter()

    def evict_closed(self, window_end_ns: int | None, rank_id: str | None = None) -> None:
        if window_end_ns is not None:
            rank_text = str(rank_id) if rank_id is not None else None
            expired = [
                raw
                for raw in self.primary_by_raw
                if (rank_text is None or raw[0] == rank_text) and int(raw[7]) <= window_end_ns
            ]
            for raw in expired:
                self.primary_by_raw.pop(raw, None)
                self.presentation_counts.pop(raw, None)
        while len(self.primary_by_raw) > _MAX_ACTIVE_RAW_CARRYOVER:
            oldest = next(iter(self.primary_by_raw))
            self.primary_by_raw.pop(oldest, None)
            self.presentation_counts.pop(oldest, None)


class NativeCallWindowTracker:
    """Full-window native-call occurrence tracker independent of mapping_limit."""

    def __init__(self, global_tracker: NativeCallGlobalTracker, alias_names: set[str]) -> None:
        self._global = global_tracker
        self._alias_names = alias_names
        self._groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)

    def observe(
        self,
        event: Event,
        interval: tuple[int, int],
        correspondence: Mapping[str, Any] | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        raw = event_raw_identity(event)
        native_identity: str | None = None
        if correspondence is not None and correspondence.get("basis") == "observed_hccl_alias_same_call":
            native_identity = "observed_raw_identity"
        elif raw is None and (
            event.op_type in self._alias_names or event.name in self._alias_names
        ):
            native_identity = "unresolved_alias_without_relational_keys"

        if native_identity is not None:
            self._global.identity_counts[native_identity] += 1

        if (
            correspondence is None
            or correspondence.get("basis") != "observed_hccl_alias_same_call"
            or raw is None
        ):
            return native_identity, None

        call = correspondence.get("native_call") or {}
        presentation_id = f"{event.event_id}:{event.op_type}"
        primary = self._global.primary_by_raw.setdefault(raw, presentation_id)
        self._global.presentation_counts[raw] += 1
        index = self._global.presentation_counts[raw]
        occurrence: dict[str, Any] = {
            "call_id": call.get("call_id"),
            "raw_identity": dict(correspondence.get("raw_identity") or {}),
            "charge": "call",
            "call_owner": (call.get("timing_owner") or {}).get("op_id"),
            "primary_presentation": primary,
            "alias_of": None if presentation_id == primary else primary,
            "presentation_id": presentation_id,
            "presentation_index": index,
            "occurrence_key": list(raw),
        }
        self._groups[raw].append(
            {
                "event_id": event.event_id,
                "interval": interval,
                "occurrence": occurrence,
            }
        )
        return native_identity, occurrence

    def finish(
        self,
        *,
        window_end_ns: int | None = None,
        rank_id: str | None = None,
    ) -> list[dict[str, Any]]:
        native_calls: list[dict[str, Any]] = []
        for raw, entries in self._groups.items():
            presentations = [entry["occurrence"]["presentation_id"] for entry in entries]
            for entry in entries:
                entry["occurrence"].update(
                    presentations=presentations,
                    presentation_count=len(presentations),
                )
            first_occ = entries[0]["occurrence"]
            intervals = [entry["interval"] for entry in entries]
            native_calls.append(
                {
                    "call_id": first_occ.get("call_id"),
                    "rank_id": raw[0],
                    "raw_identity": first_occ.get("raw_identity"),
                    "charge": "call",
                    "call_owner": first_occ.get("call_owner"),
                    "presentation_count": len(presentations),
                    "presentations": presentations,
                    "representative_event_id": entries[0]["event_id"],
                    "activity_ns": _union_ns(intervals),
                    "accounting_basis": "one_call_alias_union_not_sum_of_presentations",
                }
            )
        self._global.evict_closed(window_end_ns, rank_id)
        return native_calls


__all__ = [
    "NativeCallGlobalTracker",
    "NativeCallWindowTracker",
    "event_raw_identity",
    "event_signature",
    "native_call_signature_match",
    "resolve_implementation_correspondence",
    "verify_graph_id",
]
