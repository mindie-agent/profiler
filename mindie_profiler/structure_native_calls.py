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

_MISSING_TEXT = frozenset({"", "N/A", "NULL", "NONE", "UNDEFINED"})
_UNDEFINED_DTYPES = frozenset({"", "N/A", "NULL", "NONE", "UNDEFINED", "DT_UNDEFINED"})
_ATTENTION_AUX_DTYPES = frozenset(
    {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "bool"}
)
_DTYPE_TOKENS = {
    **dict.fromkeys(("BF16", "BFP16", "BFLOAT16", "DT_BF16", "DT_BFLOAT16"), "bf16"),
    **dict.fromkeys(("FP16", "HALF", "FLOAT16", "DT_FLOAT16", "DT_HALF"), "fp16"),
    **dict.fromkeys(("FP32", "FLOAT", "FLOAT32", "DT_FLOAT", "DT_FLOAT32"), "fp32"),
    **dict.fromkeys(("FP64", "DOUBLE", "FLOAT64", "DT_DOUBLE", "DT_FLOAT64"), "fp64"),
    **dict.fromkeys(("INT4", "DT_INT4"), "int4"),
    **dict.fromkeys(("INT8", "DT_INT8"), "int8"),
    **dict.fromkeys(("INT16", "DT_INT16"), "int16"),
    **dict.fromkeys(("INT32", "DT_INT32"), "int32"),
    **dict.fromkeys(("INT64", "DT_INT64"), "int64"),
    **dict.fromkeys(("UINT8", "DT_UINT8"), "uint8"),
    **dict.fromkeys(("UINT16", "DT_UINT16"), "uint16"),
    **dict.fromkeys(("UINT32", "DT_UINT32"), "uint32"),
    **dict.fromkeys(("UINT64", "DT_UINT64"), "uint64"),
    **dict.fromkeys(("BOOL", "DT_BOOL"), "bool"),
    **dict.fromkeys(("HIF8", "HIFLOAT8", "DT_HIFLOAT8"), "hif8"),
    **dict.fromkeys(("FP8_E4M3", "FP8_E4M3FN", "FLOAT8_E4M3FN", "DT_FLOAT8_E4M3FN"), "fp8_e4m3"),
    **dict.fromkeys(("FP8_E5M2", "FLOAT8_E5M2", "DT_FLOAT8_E5M2"), "fp8_e5m2"),
    **dict.fromkeys(("FP8_E8M0", "FLOAT8_E8M0", "DT_FLOAT8_E8M0"), "fp8_e8m0"),
    **dict.fromkeys(("MXFP4", "FLOAT4_E2M1", "DT_FLOAT4_E2M1"), "mxfp4"),
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
    upper = text.upper()
    if upper in _UNDEFINED_DTYPES:
        return None
    return _DTYPE_TOKENS.get(upper, text.lower().removeprefix("dt_"))


def _parse_paired_lanes(
    shapes_text: str | None,
    dtypes_text: str | None,
    formats_text: str | None = None,
) -> tuple[str, tuple[tuple[int, ...], ...], tuple[str, ...], tuple[str, ...]]:
    s_whole = str(shapes_text or "").strip().strip('"')
    d_whole = str(dtypes_text or "").strip().strip('"')
    f_whole = str(formats_text or "").strip().strip('"')
    if s_whole.upper() in _MISSING_TEXT or d_whole.upper() in _MISSING_TEXT:
        return "missing", (), (), ()
    s_parts = s_whole.split(";")
    d_parts = d_whole.split(";")
    if len(s_parts) != len(d_parts):
        return "mismatch", (), (), ()
    has_formats = f_whole.upper() not in _MISSING_TEXT
    f_parts = f_whole.split(";") if has_formats else None
    if f_parts is not None and len(f_parts) != len(d_parts):
        return "mismatch", (), (), ()
    shapes: list[tuple[int, ...]] = []
    dtypes: list[str] = []
    formats: list[str] = []
    for idx, raw_d in enumerate(d_parts):
        s_cell = s_parts[idx].strip().strip('"')
        d_cell = raw_d.strip().strip('"')
        f_cell = f_parts[idx].strip().strip('"').upper() if f_parts is not None else ""
        if d_cell.upper() in _UNDEFINED_DTYPES:
            if s_cell.upper() in _MISSING_TEXT:
                continue
            return "missing", (), (), ()
        dt = _norm_dtype(d_cell)
        if dt is None or s_cell.upper() in {"N/A", "NULL", "NONE", "UNDEFINED"}:
            return "missing", (), (), ()
        if s_cell == "":
            dims: tuple[int, ...] = ()
        else:
            try:
                dims = tuple(int(value) for value in s_cell.split(",") if value.strip())
            except ValueError:
                return "missing", (), (), ()
            if not dims:
                return "missing", (), (), ()
        shapes.append(dims)
        dtypes.append(dt)
        if f_parts is not None:
            if f_cell in _MISSING_TEXT:
                return "missing", (), (), ()
            formats.append(f_cell)
    if not shapes:
        return "missing", (), (), ()
    return "ok", tuple(shapes), tuple(dtypes), tuple(formats)


def event_signature(
    event: Event,
) -> tuple[tuple[tuple[int, ...], ...], tuple[str, ...]] | None:
    """Parsed shape/dtype lanes of a captured event, or None when incomplete."""
    in_status, inputs, input_dtypes, _ = _parse_paired_lanes(
        event.input_shapes, event.input_dtypes, event.input_formats
    )
    out_status, outputs, output_dtypes, _ = _parse_paired_lanes(
        event.output_shapes, event.output_dtypes, event.output_formats
    )
    if in_status != "ok" or out_status != "ok":
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
    *,
    in_dtypes: tuple[str, ...] = (),
    out_dtypes: tuple[str, ...] = (),
    family: str = "",
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

    is_attention_abi = family.lower() == "attention" or "query" in input_roles
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
        effective_out = out_shapes
        if is_attention_abi and len(out_shapes) > len(output_roles):
            extra_ok = all(
                out_shapes[idx] == ()
                and (idx >= len(out_dtypes) or out_dtypes[idx] in {"fp32", "bf16", "fp16"})
                for idx in range(len(output_roles), len(out_shapes))
            )
            if extra_ok:
                effective_out = out_shapes[: len(output_roles)]
        if Counter(effective_out) != Counter(output_roles.values()):
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
        if is_attention_abi and in_dtypes:
            obs_counts = Counter(
                shape
                for shape, dt in zip(in_shapes, in_dtypes)
                if dt not in _ATTENTION_AUX_DTYPES and shape != ()
            )
        else:
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
    in_status, in_shapes, in_dtypes, in_formats = _parse_paired_lanes(
        event.input_shapes, event.input_dtypes, event.input_formats
    )
    out_status, out_shapes, out_dtypes, out_formats = _parse_paired_lanes(
        event.output_shapes, event.output_dtypes, event.output_formats
    )
    if in_status == "mismatch" or out_status == "mismatch":
        return False
    if in_status != "ok" or out_status != "ok":
        return None

    typed = binding.get("typed") or {}
    attrs = typed.get("attrs") if isinstance(typed.get("attrs"), Mapping) else {}
    shapes_map = typed.get("shapes") if isinstance(typed.get("shapes"), Mapping) else {}
    family = str(binding.get("family") or "")
    is_attention_abi = family.lower() == "attention" or any(
        str(k).strip().lower() == "query" for k in shapes_map
    )
    shape_verdict = _match_declared_shapes(
        typed.get("shapes"),
        in_shapes,
        out_shapes,
        in_dtypes=in_dtypes,
        out_dtypes=out_dtypes,
        family=family,
    )
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
            "query_dtype",
            "key_dtype",
            "value_dtype",
            "weight_dtype",
            "cache_dtype",
            "group_list_dtype",
            "index_dtype",
            "scale_dtype",
            "input_scale_dtype",
        ):
            if (aux := _norm_dtype(typed.get(key) or attrs.get(key))) is not None:
                allowed_in.add(aux)
        checked_in = (
            tuple(
                dt
                for shape, dt in zip(in_shapes, in_dtypes)
                if dt not in _ATTENTION_AUX_DTYPES and shape != ()
            )
            if is_attention_abi
            else in_dtypes
        )
        if in_dtypes[0] != declared_dtype or any(dt not in allowed_in for dt in checked_in):
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
            checked_out = (
                tuple(dt for shape, dt in zip(out_shapes, out_dtypes) if shape != ())
                if is_attention_abi
                else out_dtypes
            )
            if out_dtypes[0] != target_out or any(dt not in allowed_out for dt in checked_out):
                return False

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
            _parse_paired_lanes(event.input_shapes, event.input_dtypes, event.input_formats),
            _parse_paired_lanes(event.output_shapes, event.output_dtypes, event.output_formats),
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

    impl_targets = (
        list(
            dict.fromkeys(
                rank_candidates_fn(target_index.native_implementations.get(kind, ()), rank)
            )
        )
        if not targets
        else []
    )
    bound_verdicts: list[tuple[str, bool | None]] = []
    if impl_targets and event is not None:
        bound_verdicts = [
            (node, native_call_signature_match(target_index.native_bindings[node], event))
            for node in impl_targets
            if node in target_index.native_bindings
        ]
        matched_impl = [node for node, verdict in bound_verdicts if verdict is True]
        if matched_impl:
            targets = matched_impl
            signature_match = True
            basis = "declared_native_call_signature"

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
            elif not impl_targets:
                targets = candidates
                matched_label = candidate_name
                basis = "declared_native_call_no_event"
                break

    if not targets and impl_targets:
        targets = impl_targets
        basis = "declared_native_implementation"
        if bound_verdicts:
            verdict_set = {verdict for _, verdict in bound_verdicts}
            if False in verdict_set and None not in verdict_set:
                signature_match = False

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
